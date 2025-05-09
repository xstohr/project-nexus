"""Lambda function for creating workspaces."""

import json
from ...shared.utils.utils import build_response, get_user_from_event, accounts_table, logger
from ...shared.models.workspace_models import create_workspace_item, create_workspace_user_role_item, validate_workspace_input

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
        
        # Validate input
        workspace_data = {
            "workspace_name": body.get("workspace_name"),
            "account_id": account_id
        }
        is_valid, error_msg = validate_workspace_input(workspace_data)
        if not is_valid:
            return build_response(400, {"error": error_msg})
        
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
        workspace_item = create_workspace_item(
            account_id=account_id,
            workspace_name=body["workspace_name"],
            owner_id=user["user_id"],
            owner_email=user["email"]
        )
        
        # Create admin role for the user in this workspace
        user_role_item = create_workspace_user_role_item(
            account_id=account_id,
            workspace_id=workspace_item["workspace_id"],
            user_id=user["user_id"],
            email=user["email"],
            role="ADMIN"
        )
        
        # Write to DynamoDB
        accounts_table.put_item(Item=workspace_item)
        accounts_table.put_item(Item=user_role_item)
        
        logger.info(f"Workspace created: {workspace_item['workspace_id']} in account {account_id}")
        
        return build_response(201, {
            "message": "Workspace created successfully",
            "workspace_id": workspace_item["workspace_id"],
            "workspace_name": body["workspace_name"],
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        return build_response(500, {"error": "Failed to create workspace"}) 