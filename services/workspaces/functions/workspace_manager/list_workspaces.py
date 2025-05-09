"""Lambda function for listing workspaces for an account."""

import json
from ..common.utils import build_response, get_user_from_event, accounts_table, logger

def handler(event, context):
    """Handle workspace listing requests."""
    try:
        # Get account_id from path parameters
        account_id = event.get("pathParameters", {}).get("accountId")
        if not account_id:
            return build_response(400, {"error": "Missing accountId parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Query workspaces for the account
        response = accounts_table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"ACCOUNT#{account_id}",
                ":sk_prefix": "WORKSPACE#"
            }
        )
        
        # Extract workspace details
        workspaces = []
        for item in response.get("Items", []):
            if item.get("entity_type") == "WORKSPACE" and item.get("status") == "ACTIVE":
                workspaces.append({
                    "workspace_id": item["workspace_id"],
                    "workspace_name": item["workspace_name"],
                    "account_id": item["account_id"],
                    "owner_id": item["owner_id"],
                    "status": item["status"],
                    "created_at": item["created_at"]
                })
        
        return build_response(200, {"workspaces": workspaces})
    
    except Exception as e:
        logger.error(f"Error listing workspaces: {str(e)}")
        return build_response(500, {"error": "Failed to list workspaces"}) 