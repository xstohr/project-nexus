"""Lambda function for creating workspaces."""

import json
from datetime import datetime
from ..common.utils import build_response, get_user_from_event, accounts_table, logger

def handler(event, context):
    """Handle workspace creation requests."""
    try:
        # Get user from the event
        user = get_user_from_event(event)
        
        # Get account_id from path parameters
        account_id = event.get("pathParameters", {}).get("accountId")
        if not account_id:
            return build_response(400, {"error": "Missing accountId parameter"})
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        if "workspace_name" not in body or not body["workspace_name"]:
            return build_response(400, {"error": "Missing workspace_name parameter"})
        
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
        
        # Create workspace item
        timestamp = datetime.utcnow().isoformat()
        workspace_id = f"ws-{timestamp.replace(':', '-')}-{user['user_id'][:6]}"
        
        workspace_item = {
            "PK": f"ACCOUNT#{account_id}",
            "SK": f"WORKSPACE#{workspace_id}",
            "workspace_id": workspace_id,
            "workspace_name": body["workspace_name"],
            "owner_id": user["user_id"],
            "account_id": account_id,
            "status": "ACTIVE",
            "created_at": timestamp,
            "updated_at": timestamp,
            "entity_type": "WORKSPACE",
            "GSI1PK": f"USER#{user['user_id']}",
            "GSI1SK": f"WORKSPACE#{workspace_id}"
        }
        
        # Create admin role for the user in this workspace
        user_role_item = {
            "PK": f"WORKSPACE#{workspace_id}",
            "SK": f"USER#{user['user_id']}",
            "account_id": account_id,
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "email": user["email"],
            "role": "ADMIN",
            "created_at": timestamp,
            "updated_at": timestamp,
            "entity_type": "USER_ROLE",
            "GSI1PK": f"USER#{user['user_id']}",
            "GSI1SK": f"WORKSPACE#{workspace_id}"
        }
        
        # Write to DynamoDB
        accounts_table.put_item(Item=workspace_item)
        accounts_table.put_item(Item=user_role_item)
        
        logger.info(f"Workspace created: {workspace_id} in account {account_id}")
        
        return build_response(201, {
            "message": "Workspace created successfully",
            "workspace_id": workspace_id,
            "workspace_name": body["workspace_name"],
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        return build_response(500, {"error": "Failed to create workspace"}) 