"""Lambda function to delete a task."""

import os
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, get_task_by_id, validate_workspace_access

# Initialize logger
logger = Logger(service="TasksService")

# Get the table name from environment variables
TASKS_TABLE = os.environ.get('TASKS_TABLE', 'Tasks')

# Initialize DynamoDB resource
import boto3
dynamodb = boto3.resource('dynamodb')
tasks_table = dynamodb.Table(TASKS_TABLE)

@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    """Handle task deletion request."""
    logger.info("Delete task request received")
    
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
        
        # Get the task to ensure it exists and belongs to the workspace
        existing_task = get_task_by_id(workspace_id, task_id)
        if not existing_task:
            return build_response(404, {"message": f"Task with ID {task_id} not found"})
        
        # Delete the task from DynamoDB
        tasks_table.delete_item(
            Key={
                "PK": f"WORKSPACE#{workspace_id}",
                "SK": f"TASK#{task_id}"
            }
        )
        
        # Return success response
        return build_response(200, {
            "message": "Task deleted successfully",
            "task_id": task_id,
            "workspace_id": workspace_id
        })
        
    except Exception as e:
        logger.exception("Error deleting task")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 