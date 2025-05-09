"""Account Management Lambda Function."""

import json
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

from ..common.utils import build_response, get_user_from_event, logger, accounts_table
from ..common.models import create_account_item, validate_account_input, create_user_role_item

def lambda_handler(event, context):
    """Main handler for account management events."""
    http_method = event.get("httpMethod", "").lower()
    resource_path = event.get("resource", "")
    
    # Route request to appropriate function
    if resource_path == "/accounts":
        if http_method == "post":
            return create_account(event, context)
        elif http_method == "get":
            return list_accounts(event, context)
    elif resource_path == "/accounts/{accountId}":
        if http_method == "get":
            return get_account(event, context)
        elif http_method == "put":
            return update_account(event, context)
        elif http_method == "delete":
            return delete_account(event, context)
    
    # If no matching route found
    return build_response(400, {"error": "Invalid request path or method"})

def create_account(event, context):
    """Create a new account."""
    try:
        # Get user from the event
        user = get_user_from_event(event)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        
        # Validate input
        is_valid, error_msg = validate_account_input(body)
        if not is_valid:
            return build_response(400, {"error": error_msg})
        
        # Create account item
        account_item = create_account_item(
            account_name=body["account_name"],
            owner_id=user["user_id"],
            owner_email=body.get("owner_email", user["email"])
        )
        
        # Create admin role for the user
        user_role_item = create_user_role_item(
            account_id=account_item["account_id"],
            workspace_id=None,  # Account-level role
            user_id=user["user_id"],
            email=user["email"],
            role="ADMIN"
        )
        
        # Write to DynamoDB
        accounts_table.put_item(Item=account_item)
        accounts_table.put_item(Item=user_role_item)
        
        logger.info(f"Account created: {account_item['account_id']}")
        
        return build_response(201, {
            "message": "Account created successfully",
            "account_id": account_item["account_id"],
            "account_name": account_item["account_name"]
        })
    
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        return build_response(500, {"error": "Failed to create account"})

def get_account(event, context):
    """Get account details."""
    try:
        # Get account_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        if not account_id:
            return build_response(400, {"error": "Missing account_id parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Get account from DynamoDB
        response = accounts_table.get_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            }
        )
        
        # Check if account exists
        account = response.get("Item")
        if not account:
            return build_response(404, {"error": "Account not found"})
        
        # Return account details
        return build_response(200, {
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "owner_email": account["owner_email"],
            "status": account["status"],
            "tier": account["tier"],
            "created_at": account["created_at"]
        })
    
    except Exception as e:
        logger.error(f"Error retrieving account: {str(e)}")
        return build_response(500, {"error": "Failed to retrieve account"})

def update_account(event, context):
    """Update account details."""
    try:
        # Get account_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        if not account_id:
            return build_response(400, {"error": "Missing account_id parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        if not body:
            return build_response(400, {"error": "Request body is required"})
        
        # Check if account exists
        response = accounts_table.get_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            }
        )
        
        account = response.get("Item")
        if not account:
            return build_response(404, {"error": "Account not found"})
        
        # Prepare update expression
        update_expression = "SET "
        expression_attribute_values = {}
        
        # Handle updateable fields
        updatable_fields = {
            "account_name": "account_name",
            "status": "status",
            "tier": "tier"
        }
        
        for field, attr_name in updatable_fields.items():
            if field in body and body[field]:
                update_expression += f"{attr_name} = :{field}, "
                expression_attribute_values[f":{field}"] = body[field]
        
        # Add updated_at timestamp
        update_expression += "updated_at = :updated_at"
        expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
        
        # Update account in DynamoDB
        accounts_table.update_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Account updated: {account_id}")
        
        return build_response(200, {
            "message": "Account updated successfully",
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        return build_response(500, {"error": "Failed to update account"})

def delete_account(event, context):
    """Delete an account (mark as inactive)."""
    try:
        # Get account_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        if not account_id:
            return build_response(400, {"error": "Missing account_id parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Check if account exists
        response = accounts_table.get_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            }
        )
        
        account = response.get("Item")
        if not account:
            return build_response(404, {"error": "Account not found"})
        
        # Mark account as inactive rather than deleting
        accounts_table.update_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            },
            UpdateExpression="SET status = :status, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":status": "INACTIVE",
                ":updated_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Account marked as inactive: {account_id}")
        
        return build_response(200, {
            "message": "Account marked as inactive",
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error deactivating account: {str(e)}")
        return build_response(500, {"error": "Failed to deactivate account"})

def list_accounts(event, context):
    """List accounts for a user."""
    try:
        # Get user from the event
        user = get_user_from_event(event)
        
        # Query accounts where user has a role
        response = accounts_table.query(
            IndexName="UserRolesIndex",  # We'd need to create this GSI
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={
                ":user_id": user["user_id"]
            }
        )
        
        # Extract account IDs
        account_ids = []
        for item in response.get("Items", []):
            if "account_id" in item and item["account_id"] not in account_ids:
                account_ids.append(item["account_id"])
        
        # Get account details for each account ID
        accounts = []
        for account_id in account_ids:
            account_response = accounts_table.get_item(
                Key={
                    "PK": f"ACCOUNT#{account_id}",
                    "SK": "METADATA"
                }
            )
            
            account = account_response.get("Item")
            if account and account["status"] == "ACTIVE":
                accounts.append({
                    "account_id": account["account_id"],
                    "account_name": account["account_name"],
                    "status": account["status"],
                    "tier": account["tier"],
                    "created_at": account["created_at"]
                })
        
        return build_response(200, {"accounts": accounts})
    
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        return build_response(500, {"error": "Failed to list accounts"}) 