"""Lambda function to update an existing task."""

import json
import os
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, get_task_by_id, validate_workspace_access
from ...shared.models.task_models import validate_task_input, prepare_update_expression

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
    """Handle task update request."""
    logger.info("Update task request received")
    
    try:
        # Extract user information from the event context
        user = get_user_from_event(event)
        if not user:
            return build_response(401, {"message": "Unauthorized: User not authenticated"})

        # Parse the body from the event
        if 'body' not in event or not event['body']:
            return build_response(400, {"message": "Missing request body"})
        
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return build_response(400, {"message": "Invalid JSON in request body"})
        
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
        
        # Get the existing task
        existing_task = get_task_by_id(workspace_id, task_id)
        if not existing_task:
            return build_response(404, {"message": f"Task with ID {task_id} not found"})
        
        # Validate task update data
        is_valid, validation_error = validate_task_input(body)
        if not is_valid:
            return build_response(400, {"message": validation_error})
        
        # Store existing task in body for update expression preparation
        body["_existing_task"] = existing_task
        
        # Prepare update expression for DynamoDB
        update_expr, expr_attr_values, expr_attr_names = prepare_update_expression(body)
        
        # Update the task in DynamoDB
        update_response = tasks_table.update_item(
            Key={
                "PK": f"WORKSPACE#{workspace_id}",
                "SK": f"TASK#{task_id}"
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names,
            ReturnValues="ALL_NEW"
        )
        
        # Get the updated task
        updated_task = update_response.get('Attributes', {})
        
        # Prepare response with updated task details
        response_data = {
            "message": "Task updated successfully",
            "task": {
                "task_id": updated_task.get("task_id", task_id),
                "title": updated_task.get("title"),
                "workspace_id": updated_task.get("workspace_id", workspace_id),
                "status": updated_task.get("status"),
                "priority": updated_task.get("priority"),
                "created_at": updated_task.get("created_at"),
                "updated_at": updated_task.get("updated_at"),
                "created_by": updated_task.get("created_by")
            }
        }
        
        # Add optional fields to response if they exist
        optional_fields = ["description", "assignee_id", "due_date", "tags"]
        for field in optional_fields:
            if field in updated_task:
                response_data["task"][field] = updated_task[field]
        
        return build_response(200, response_data)
        
    except Exception as e:
        logger.exception("Error updating task")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 