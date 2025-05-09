"""Account Management Lambda function for the Nexus app."""

import json
import os
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Initialize clients
dynamodb = boto3.resource("dynamodb")
cognito_idp = boto3.client("cognito-idp")

# Environment variables
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE")
USER_POOL_ID = os.environ.get("USER_POOL_ID")

# Constants
USER_ROLES = {
    "ADMIN": "Administrator with full system access",
    "SUPER_USER": "Power user with workspace-level administration",
    "BASIC_USER": "Regular user with limited permissions"
}

# Initialize DynamoDB table
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)

# Helper functions
def get_user_from_event(event):
    """Extract the authenticated user from event context."""
    # In a production environment, this would come from a JWT token or Cognito claims
    # For development, we'll extract from headers or use a default
    auth_header = event.get("headers", {}).get("Authorization", "")
    
    # Extract user info (simplified for now)
    # In production, this would properly decode and validate the JWT
    if auth_header.startswith("Bearer "):
        # Simulate extracting user from token
        return {
            "user_id": "test-user-id",  # Would come from token
            "email": "test@example.com",  # Would come from token
            "tenant_id": "test-tenant-id"  # Would come from token
        }
    
    # Default for testing
    return {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "tenant_id": "test-tenant-id"
    }

def generate_pk_sk(entity_type, entity_id, subtype=None):
    """Generate primary key and sort key for DynamoDB."""
    pk = f"{entity_type}#{entity_id}"
    sk = "METADATA" if subtype is None else f"{subtype}"
    return pk, sk

def build_response(status_code, body):
    """Build a standard API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }

# Account Management Endpoints
@app.post("/accounts")
def create_account():
    """Create a new account (tenant)."""
    try:
        # Get request body
        body = app.current_event.json_body
        
        # Required fields
        account_name = body.get("name")
        
        if not account_name:
            return build_response(400, {"message": "Account name is required"})
        
        # Generate account ID
        account_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()
        
        # Create account record
        account_item = {
            "PK": f"ACCOUNT#{account_id}",
            "SK": "METADATA",
            "id": account_id,
            "name": account_name,
            "status": "ACTIVE",
            "createdAt": current_time,
            "updatedAt": current_time,
            "type": "ACCOUNT"
        }
        
        # Optional fields
        if "description" in body:
            account_item["description"] = body["description"]
        
        # Save to DynamoDB
        accounts_table.put_item(Item=account_item)
        
        # Return success with created account
        account_item.pop("PK")
        account_item.pop("SK")
        
        return account_item
    
    except Exception as e:
        logger.exception("Error creating account")
        return build_response(500, {"message": f"Error creating account: {str(e)}"})

@app.get("/accounts/{accountId}")
def get_account(accountId):
    """Get account details."""
    try:
        # Get the account from DynamoDB
        pk, sk = generate_pk_sk("ACCOUNT", accountId)
        
        response = accounts_table.get_item(
            Key={"PK": pk, "SK": sk}
        )
        
        # Check if account exists
        if "Item" not in response:
            return build_response(404, {"message": f"Account with ID {accountId} not found"})
        
        # Return account data (excluding internal keys)
        account = response["Item"]
        account.pop("PK")
        account.pop("SK")
        
        return account
    
    except Exception as e:
        logger.exception(f"Error getting account {accountId}")
        return build_response(500, {"message": f"Error getting account: {str(e)}"})

@app.put("/accounts/{accountId}")
def update_account(accountId):
    """Update an existing account."""
    try:
        # Get the current account
        pk, sk = generate_pk_sk("ACCOUNT", accountId)
        
        response = accounts_table.get_item(
            Key={"PK": pk, "SK": sk}
        )
        
        # Check if account exists
        if "Item" not in response:
            return build_response(404, {"message": f"Account with ID {accountId} not found"})
        
        # Get the updated data
        body = app.current_event.json_body
        current_account = response["Item"]
        
        # Create update expression
        update_expression = "SET updatedAt = :updatedAt"
        expression_values = {
            ":updatedAt": datetime.utcnow().isoformat()
        }
        
        # Handle fields that can be updated
        updateable_fields = ["name", "description", "status"]
        
        for field in updateable_fields:
            if field in body:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = body[field]
        
        # Update the account
        accounts_table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        
        # Return the updated account
        return build_response(200, {"message": f"Account {accountId} updated successfully"})
    
    except Exception as e:
        logger.exception(f"Error updating account {accountId}")
        return build_response(500, {"message": f"Error updating account: {str(e)}"})

# Workspace Management Endpoints
@app.post("/accounts/{accountId}/workspaces")
def create_workspace(accountId):
    """Create a new workspace within an account."""
    try:
        # Check if account exists
        pk, sk = generate_pk_sk("ACCOUNT", accountId)
        
        response = accounts_table.get_item(
            Key={"PK": pk, "SK": sk}
        )
        
        if "Item" not in response:
            return build_response(404, {"message": f"Account with ID {accountId} not found"})
        
        # Get request body
        body = app.current_event.json_body
        
        # Required fields
        workspace_name = body.get("name")
        
        if not workspace_name:
            return build_response(400, {"message": "Workspace name is required"})
        
        # Generate workspace ID
        workspace_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()
        
        # Create workspace record
        workspace_item = {
            "PK": f"WORKSPACE#{workspace_id}",
            "SK": "METADATA",
            "GSI1PK": f"ACCOUNT#{accountId}",
            "GSI1SK": f"WORKSPACE#{workspace_id}",
            "id": workspace_id,
            "accountId": accountId,
            "name": workspace_name,
            "status": "ACTIVE",
            "createdAt": current_time,
            "updatedAt": current_time,
            "type": "WORKSPACE"
        }
        
        # Optional fields
        if "description" in body:
            workspace_item["description"] = body["description"]
        
        # Save to DynamoDB
        accounts_table.put_item(Item=workspace_item)
        
        # Return success with created workspace
        workspace_response = {
            "id": workspace_id,
            "accountId": accountId,
            "name": workspace_name,
            "status": "ACTIVE",
            "createdAt": current_time
        }
        
        if "description" in body:
            workspace_response["description"] = body["description"]
        
        return workspace_response
    
    except Exception as e:
        logger.exception(f"Error creating workspace in account {accountId}")
        return build_response(500, {"message": f"Error creating workspace: {str(e)}"})

@app.get("/accounts/{accountId}/workspaces")
def get_workspaces(accountId):
    """Get all workspaces for an account."""
    try:
        # Check if account exists
        account_pk, account_sk = generate_pk_sk("ACCOUNT", accountId)
        
        account_response = accounts_table.get_item(
            Key={"PK": account_pk, "SK": account_sk}
        )
        
        if "Item" not in account_response:
            return build_response(404, {"message": f"Account with ID {accountId} not found"})
        
        # Query workspaces for this account using GSI1
        response = accounts_table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :account_id AND begins_with(GSI1SK, :workspace_prefix)",
            ExpressionAttributeValues={
                ":account_id": f"ACCOUNT#{accountId}",
                ":workspace_prefix": "WORKSPACE#"
            }
        )
        
        # Format response
        workspaces = []
        for item in response.get("Items", []):
            workspace = {
                "id": item["id"],
                "name": item["name"],
                "status": item["status"],
                "accountId": item["accountId"],
                "createdAt": item["createdAt"],
                "updatedAt": item["updatedAt"]
            }
            
            if "description" in item:
                workspace["description"] = item["description"]
            
            workspaces.append(workspace)
        
        return {
            "workspaces": workspaces,
            "count": len(workspaces)
        }
    
    except Exception as e:
        logger.exception(f"Error getting workspaces for account {accountId}")
        return build_response(500, {"message": f"Error getting workspaces: {str(e)}"})

@app.get("/workspaces/{workspaceId}")
def get_workspace(workspaceId):
    """Get details of a specific workspace."""
    try:
        # Get the workspace from DynamoDB
        pk, sk = generate_pk_sk("WORKSPACE", workspaceId)
        
        response = accounts_table.get_item(
            Key={"PK": pk, "SK": sk}
        )
        
        # Check if workspace exists
        if "Item" not in response:
            return build_response(404, {"message": f"Workspace with ID {workspaceId} not found"})
        
        # Return workspace data (excluding internal keys)
        workspace = response["Item"]
        
        # Format response
        workspace_response = {
            "id": workspace["id"],
            "name": workspace["name"],
            "status": workspace["status"],
            "accountId": workspace["accountId"],
            "createdAt": workspace["createdAt"],
            "updatedAt": workspace["updatedAt"]
        }
        
        if "description" in workspace:
            workspace_response["description"] = workspace["description"]
        
        return workspace_response
    
    except Exception as e:
        logger.exception(f"Error getting workspace {workspaceId}")
        return build_response(500, {"message": f"Error getting workspace: {str(e)}"})

# User Role Management Endpoints
@app.post("/accounts/{accountId}/users/{userId}/roles")
def assign_user_role(accountId, userId):
    """Assign a role to a user within an account."""
    try:
        # Get request body
        body = app.current_event.json_body
        
        # Required fields
        role = body.get("role")
        
        if not role or role not in USER_ROLES:
            valid_roles = ", ".join(USER_ROLES.keys())
            return build_response(400, {
                "message": f"Invalid role. Must be one of: {valid_roles}"
            })
        
        # Check if account exists
        account_pk, account_sk = generate_pk_sk("ACCOUNT", accountId)
        
        account_response = accounts_table.get_item(
            Key={"PK": account_pk, "SK": account_sk}
        )
        
        if "Item" not in account_response:
            return build_response(404, {"message": f"Account with ID {accountId} not found"})
        
        # Try to get the user from Cognito (would be implemented in production)
        # For now, we'll just assume the user exists
        
        # Create the user role mapping
        current_time = datetime.utcnow().isoformat()
        
        role_mapping = {
            "PK": f"ACCOUNT#{accountId}",
            "SK": f"USER#{userId}",
            "GSI1PK": f"USER#{userId}",
            "GSI1SK": f"ACCOUNT#{accountId}",
            "userId": userId,
            "accountId": accountId,
            "role": role,
            "createdAt": current_time,
            "updatedAt": current_time,
            "type": "USER_ROLE"
        }
        
        # Save to DynamoDB
        accounts_table.put_item(Item=role_mapping)
        
        # Return success
        return {
            "userId": userId,
            "accountId": accountId,
            "role": role,
            "createdAt": current_time
        }
    
    except Exception as e:
        logger.exception(f"Error assigning role to user {userId} in account {accountId}")
        return build_response(500, {"message": f"Error assigning role: {str(e)}"})

@app.get("/users/{userId}/roles")
def get_user_roles(userId):
    """Get all roles for a user across accounts."""
    try:
        # Query roles for this user using GSI1
        response = accounts_table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :user_id",
            ExpressionAttributeValues={
                ":user_id": f"USER#{userId}"
            }
        )
        
        # Format response
        roles = []
        for item in response.get("Items", []):
            if item.get("type") == "USER_ROLE":
                role = {
                    "userId": item["userId"],
                    "accountId": item["accountId"],
                    "role": item["role"],
                    "createdAt": item["createdAt"]
                }
                
                # Try to get account name
                try:
                    account_response = accounts_table.get_item(
                        Key={"PK": f"ACCOUNT#{item['accountId']}", "SK": "METADATA"}
                    )
                    if "Item" in account_response:
                        role["accountName"] = account_response["Item"]["name"]
                except Exception:
                    # Log but continue if we can't get account name
                    logger.warning(f"Could not retrieve account name for {item['accountId']}")
                
                roles.append(role)
        
        return {
            "userId": userId,
            "roles": roles,
            "count": len(roles)
        }
    
    except Exception as e:
        logger.exception(f"Error getting roles for user {userId}")
        return build_response(500, {"message": f"Error getting user roles: {str(e)}"})

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """Lambda handler for the account management endpoints."""
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Unhandled error in account management Lambda")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error",
                "error": str(e)
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        } 