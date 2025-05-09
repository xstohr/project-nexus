"""User Role Management Lambda Function."""

import json
from datetime import datetime
from botocore.exceptions import ClientError

from ..common.utils import build_response, get_user_from_event, logger, accounts_table, validate_role
from ..common.models import create_user_role_item

def lambda_handler(event, context):
    """Main handler for user role management events."""
    http_method = event.get("httpMethod", "").lower()
    resource_path = event.get("resource", "")
    
    # Route request to appropriate function
    if resource_path == "/accounts/{accountId}/users/roles":
        if http_method == "post":
            return assign_role(event, context)
        elif http_method == "get":
            return list_user_roles(event, context)
    elif resource_path == "/accounts/{accountId}/users/{userId}/roles":
        if http_method == "put":
            return update_role(event, context)
        elif http_method == "delete":
            return remove_role(event, context)
    elif resource_path == "/workspaces/{workspaceId}/users/roles":
        if http_method == "post":
            # Same function for workspace roles, the workspace_id will be in path params
            return assign_role(event, context)
        elif http_method == "get":
            return list_user_roles(event, context)
    elif resource_path == "/workspaces/{workspaceId}/users/{userId}/roles":
        if http_method == "put":
            return update_role(event, context)
        elif http_method == "delete":
            return remove_role(event, context)
    
    # If no matching route found
    return build_response(400, {"error": "Invalid request path or method"})

def assign_role(event, context):
    """Assign a role to a user for an account or workspace."""
    try:
        # Get user from the event
        current_user = get_user_from_event(event)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        
        # Validate required fields
        required_fields = ["user_id", "email", "role"]
        for field in required_fields:
            if field not in body or not body[field]:
                return build_response(400, {"error": f"Missing required field: {field}"})
        
        # Validate role
        is_valid, error_msg = validate_role(body["role"])
        if not is_valid:
            return build_response(400, {"error": error_msg})
        
        # Get account_id and workspace_id from path parameters or body
        account_id = event.get("pathParameters", {}).get("account_id") or body.get("account_id")
        workspace_id = event.get("pathParameters", {}).get("workspace_id") or body.get("workspace_id")
        
        if not account_id:
            return build_response(400, {"error": "Missing account_id parameter"})
        
        # Check if account exists
        account_response = accounts_table.get_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": "METADATA"
            }
        )
        
        account = account_response.get("Item")
        if not account:
            return build_response(404, {"error": "Account not found"})
        
        # If workspace_id is provided, verify it exists
        if workspace_id:
            workspace_response = accounts_table.query(
                KeyConditionExpression="PK = :pk AND SK = :sk",
                ExpressionAttributeValues={
                    ":pk": f"ACCOUNT#{account_id}",
                    ":sk": f"WORKSPACE#{workspace_id}"
                }
            )
            
            if not workspace_response.get("Items"):
                return build_response(404, {"error": "Workspace not found"})
        
        # Create user role item
        user_role_item = create_user_role_item(
            account_id=account_id,
            workspace_id=workspace_id,
            user_id=body["user_id"],
            email=body["email"],
            role=body["role"]
        )
        
        # Write to DynamoDB
        accounts_table.put_item(Item=user_role_item)
        
        if workspace_id:
            logger.info(f"Role '{body['role']}' assigned to user {body['user_id']} for workspace {workspace_id}")
            return build_response(201, {
                "message": "Role assigned successfully",
                "account_id": account_id,
                "workspace_id": workspace_id,
                "user_id": body["user_id"],
                "role": body["role"]
            })
        else:
            logger.info(f"Role '{body['role']}' assigned to user {body['user_id']} for account {account_id}")
            return build_response(201, {
                "message": "Role assigned successfully",
                "account_id": account_id,
                "user_id": body["user_id"],
                "role": body["role"]
            })
    
    except Exception as e:
        logger.error(f"Error assigning role: {str(e)}")
        return build_response(500, {"error": "Failed to assign role"})

def update_role(event, context):
    """Update a user's role for an account or workspace."""
    try:
        # Get user from the event
        current_user = get_user_from_event(event)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        
        if "role" not in body or not body["role"]:
            return build_response(400, {"error": "Missing role in request"})
        
        # Validate role
        is_valid, error_msg = validate_role(body["role"])
        if not is_valid:
            return build_response(400, {"error": error_msg})
        
        # Get account_id, workspace_id, and user_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        workspace_id = event.get("pathParameters", {}).get("workspace_id")
        user_id = event.get("pathParameters", {}).get("user_id")
        
        if not account_id or not user_id:
            return build_response(400, {"error": "Missing required parameters"})
        
        # Define key based on whether this is workspace or account level
        if workspace_id:
            key = {
                "PK": f"WORKSPACE#{workspace_id}",
                "SK": f"USER#{user_id}"
            }
        else:
            key = {
                "PK": f"ACCOUNT#{account_id}",
                "SK": f"USER#{user_id}"
            }
        
        # Check if the role assignment exists
        response = accounts_table.get_item(Key=key)
        
        user_role = response.get("Item")
        if not user_role:
            return build_response(404, {"error": "User role not found"})
        
        # Update the role
        accounts_table.update_item(
            Key=key,
            UpdateExpression="SET role = :role, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":role": body["role"],
                ":updated_at": datetime.utcnow().isoformat()
            }
        )
        
        if workspace_id:
            logger.info(f"Role updated to '{body['role']}' for user {user_id} in workspace {workspace_id}")
            return build_response(200, {
                "message": "Role updated successfully",
                "account_id": account_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": body["role"]
            })
        else:
            logger.info(f"Role updated to '{body['role']}' for user {user_id} in account {account_id}")
            return build_response(200, {
                "message": "Role updated successfully",
                "account_id": account_id,
                "user_id": user_id,
                "role": body["role"]
            })
    
    except Exception as e:
        logger.error(f"Error updating role: {str(e)}")
        return build_response(500, {"error": "Failed to update role"})

def remove_role(event, context):
    """Remove a user's role for an account or workspace."""
    try:
        # Get user from the event
        current_user = get_user_from_event(event)
        
        # Get account_id, workspace_id, and user_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        workspace_id = event.get("pathParameters", {}).get("workspace_id")
        user_id = event.get("pathParameters", {}).get("user_id")
        
        if not account_id or not user_id:
            return build_response(400, {"error": "Missing required parameters"})
        
        # Define key based on whether this is workspace or account level
        if workspace_id:
            key = {
                "PK": f"WORKSPACE#{workspace_id}",
                "SK": f"USER#{user_id}"
            }
        else:
            key = {
                "PK": f"ACCOUNT#{account_id}",
                "SK": f"USER#{user_id}"
            }
        
        # Check if the role assignment exists
        response = accounts_table.get_item(Key=key)
        
        user_role = response.get("Item")
        if not user_role:
            return build_response(404, {"error": "User role not found"})
        
        # Delete the role assignment
        accounts_table.delete_item(Key=key)
        
        if workspace_id:
            logger.info(f"Role removed for user {user_id} in workspace {workspace_id}")
            return build_response(200, {
                "message": "Role removed successfully",
                "account_id": account_id,
                "workspace_id": workspace_id,
                "user_id": user_id
            })
        else:
            logger.info(f"Role removed for user {user_id} in account {account_id}")
            return build_response(200, {
                "message": "Role removed successfully",
                "account_id": account_id,
                "user_id": user_id
            })
    
    except Exception as e:
        logger.error(f"Error removing role: {str(e)}")
        return build_response(500, {"error": "Failed to remove role"})

def list_user_roles(event, context):
    """List all users and their roles for an account or workspace."""
    try:
        # Get user from the event
        current_user = get_user_from_event(event)
        
        # Get account_id and workspace_id from path parameters
        account_id = event.get("pathParameters", {}).get("account_id")
        workspace_id = event.get("pathParameters", {}).get("workspace_id")
        
        if not account_id:
            return build_response(400, {"error": "Missing account_id parameter"})
        
        # Define query parameters based on whether this is workspace or account level
        if workspace_id:
            pk = f"WORKSPACE#{workspace_id}"
            sk_prefix = "USER#"
        else:
            pk = f"ACCOUNT#{account_id}"
            sk_prefix = "USER#"
        
        # Query for all user roles
        response = accounts_table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": pk,
                ":sk_prefix": sk_prefix
            }
        )
        
        # Extract user role details
        user_roles = []
        for item in response.get("Items", []):
            user_roles.append({
                "user_id": item["user_id"],
                "email": item["email"],
                "role": item["role"],
                "created_at": item["created_at"],
                "updated_at": item.get("updated_at", item["created_at"])
            })
        
        if workspace_id:
            return build_response(200, {
                "account_id": account_id,
                "workspace_id": workspace_id,
                "user_roles": user_roles
            })
        else:
            return build_response(200, {
                "account_id": account_id,
                "user_roles": user_roles
            })
    
    except Exception as e:
        logger.error(f"Error listing user roles: {str(e)}")
        return build_response(500, {"error": "Failed to list user roles"}) 