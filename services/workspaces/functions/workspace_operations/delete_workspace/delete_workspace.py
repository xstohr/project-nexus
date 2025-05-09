"""Lambda function for deleting (deactivating) workspaces."""

import json
from datetime import datetime
from ...shared.utils.utils import build_response, get_user_from_event, get_workspace_by_id, accounts_table, logger

def handler(event, context):
    """Handle workspace deletion (deactivation) requests."""
    try:
        # Get workspace_id from path parameters
        workspace_id = event.get("pathParameters", {}).get("workspaceId")
        if not workspace_id:
            return build_response(400, {"error": "Missing workspaceId parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Get workspace to verify it exists and get account_id
        workspace = get_workspace_by_id(workspace_id)
        if not workspace:
            return build_response(404, {"error": "Workspace not found"})
        
        account_id = workspace["account_id"]
        
        # Mark workspace as inactive rather than deleting
        accounts_table.update_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": f"WORKSPACE#{workspace_id}"
            },
            UpdateExpression="SET status = :status, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":status": "INACTIVE",
                ":updated_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Workspace marked as inactive: {workspace_id}")
        
        return build_response(200, {
            "message": "Workspace marked as inactive",
            "workspace_id": workspace_id,
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error deactivating workspace: {str(e)}")
        return build_response(500, {"error": "Failed to deactivate workspace"}) 