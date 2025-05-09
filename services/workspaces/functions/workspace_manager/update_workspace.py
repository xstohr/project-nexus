"""Lambda function for updating workspace details."""

import json
from datetime import datetime
from ..common.utils import build_response, get_user_from_event, get_workspace_by_id, accounts_table, logger

def handler(event, context):
    """Handle workspace update requests."""
    try:
        # Get workspace_id from path parameters
        workspace_id = event.get("pathParameters", {}).get("workspaceId")
        if not workspace_id:
            return build_response(400, {"error": "Missing workspaceId parameter"})
        
        # Get user from the event
        user = get_user_from_event(event)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        if not body:
            return build_response(400, {"error": "Request body is required"})
        
        # Get workspace to verify it exists and get account_id
        workspace = get_workspace_by_id(workspace_id)
        if not workspace:
            return build_response(404, {"error": "Workspace not found"})
        
        account_id = workspace["account_id"]
        
        # Prepare update expression
        update_expression = "SET "
        expression_attribute_values = {}
        
        # Handle updateable fields
        updatable_fields = {
            "workspace_name": "workspace_name",
            "status": "status"
        }
        
        for field, attr_name in updatable_fields.items():
            if field in body and body[field]:
                update_expression += f"{attr_name} = :{field}, "
                expression_attribute_values[f":{field}"] = body[field]
        
        # Add updated_at timestamp
        update_expression += "updated_at = :updated_at"
        expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
        
        # Update workspace in DynamoDB
        accounts_table.update_item(
            Key={
                "PK": f"ACCOUNT#{account_id}",
                "SK": f"WORKSPACE#{workspace_id}"
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Workspace updated: {workspace_id}")
        
        return build_response(200, {
            "message": "Workspace updated successfully",
            "workspace_id": workspace_id,
            "account_id": account_id
        })
    
    except Exception as e:
        logger.error(f"Error updating workspace: {str(e)}")
        return build_response(500, {"error": "Failed to update workspace"}) 