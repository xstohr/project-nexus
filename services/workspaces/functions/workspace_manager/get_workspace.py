"""Lambda function for retrieving workspace details."""

import json
from ..common.utils import build_response, get_user_from_event, get_workspace_by_id, logger

def handler(event, context):
    """Handle workspace retrieval requests."""
    try:
        # Get workspace_id from path parameters
        workspace_id = event.get("pathParameters", {}).get("workspaceId")
        if not workspace_id:
            return build_response(400, {"error": "Missing workspaceId parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Get workspace from DynamoDB
        workspace = get_workspace_by_id(workspace_id)
        if not workspace:
            return build_response(404, {"error": "Workspace not found"})
        
        # Return workspace details
        return build_response(200, {
            "workspace_id": workspace["workspace_id"],
            "workspace_name": workspace["workspace_name"],
            "account_id": workspace["account_id"],
            "owner_id": workspace["owner_id"],
            "status": workspace["status"],
            "created_at": workspace["created_at"]
        })
    
    except Exception as e:
        logger.error(f"Error retrieving workspace: {str(e)}")
        return build_response(500, {"error": "Failed to retrieve workspace"}) 