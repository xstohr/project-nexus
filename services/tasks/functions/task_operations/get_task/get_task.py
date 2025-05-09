"""Lambda function to retrieve a task by ID."""

import json
import os
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, get_task_by_id, validate_workspace_access

# Initialize logger
logger = Logger(service="TasksService")

@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    """Handle get task request."""
    logger.info("Get task request received")
    
    try:
        # Extract user information from the event context
        user = get_user_from_event(event)
        if not user:
            return build_response(401, {"message": "Unauthorized: User not authenticated"})
        
        # Extract path parameters
        if 'pathParameters' not in event or not event['pathParameters']:
            return build_response(400, {"message": "Missing path parameters"})
        
        path_params = event['pathParameters']
        
        # Check for workspace_id
        if 'workspaceId' not in path_params or not path_params['workspaceId']:
            return build_response(400, {"message": "Missing workspace ID"})
        workspace_id = path_params['workspaceId']
        
        # Check for task_id
        if 'taskId' not in path_params or not path_params['taskId']:
            return build_response(400, {"message": "Missing task ID"})
        task_id = path_params['taskId']
        
        # Validate workspace access
        has_access, access_error = validate_workspace_access(user["account_id"], workspace_id)
        if not has_access:
            return build_response(403, {"message": access_error or "Access denied to workspace"})
        
        # Get the task from DynamoDB
        task = get_task_by_id(workspace_id, task_id)
        
        if not task:
            return build_response(404, {"message": f"Task with ID {task_id} not found"})
        
        # Verify that the task belongs to the specified workspace
        if task.get("workspace_id") != workspace_id:
            return build_response(404, {"message": f"Task with ID {task_id} not found in workspace {workspace_id}"})
        
        # Prepare response with task details
        response_data = {
            "task": {
                "task_id": task["task_id"],
                "title": task["title"],
                "workspace_id": task["workspace_id"],
                "status": task["status"],
                "priority": task["priority"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "created_by": task["created_by"]
            }
        }
        
        # Add optional fields to response if they exist
        optional_fields = ["description", "assignee_id", "due_date", "tags"]
        for field in optional_fields:
            if field in task:
                response_data["task"][field] = task[field]
        
        return build_response(200, response_data)
        
    except Exception as e:
        logger.exception("Error retrieving task")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 