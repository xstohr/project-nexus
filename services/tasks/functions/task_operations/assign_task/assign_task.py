"""Lambda function to assign or reassign a task."""

import json
import os
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, get_task_by_id, validate_workspace_access
from ...shared.models.task_models import get_timestamp

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
    """Handle task assignment request."""
    logger.info("Assign task request received")
    
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
        
        # Check if assignee_id is in the body
        if 'assignee_id' not in body:
            return build_response(400, {"message": "Missing assignee_id in request body"})
        
        assignee_id = body.get('assignee_id')
        
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
        
        # Prepare update expression for DynamoDB
        update_expression = "SET updated_at = :updated_at, assignee_id = :assignee_id"
        expression_attr_values = {
            ":updated_at": get_timestamp(),
            ":assignee_id": assignee_id
        }
        
        # Handle GSI2 for assignee lookup
        if assignee_id:
            # Add or update GSI2 keys for assignee lookup
            update_expression += ", GSI2PK = :gsi2pk, GSI2SK = :gsi2sk"
            expression_attr_values[":gsi2pk"] = f"WORKSPACE#{workspace_id}"
            expression_attr_values[":gsi2sk"] = f"ASSIGNEE#{assignee_id}#TASK#{task_id}"
        elif "GSI2PK" in existing_task and "GSI2SK" in existing_task:
            # Remove GSI2 keys if assignee is being removed
            update_expression += " REMOVE GSI2PK, GSI2SK"
        
        # Update the task in DynamoDB
        update_response = tasks_table.update_item(
            Key={
                "PK": f"WORKSPACE#{workspace_id}",
                "SK": f"TASK#{task_id}"
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attr_values,
            ReturnValues="ALL_NEW"
        )
        
        # Get the updated task
        updated_task = update_response.get('Attributes', {})
        
        # Prepare response
        response_data = {
            "message": "Task assignment updated successfully",
            "task": {
                "task_id": updated_task.get("task_id", task_id),
                "title": updated_task.get("title"),
                "workspace_id": updated_task.get("workspace_id", workspace_id),
                "status": updated_task.get("status"),
                "priority": updated_task.get("priority"),
                "assignee_id": updated_task.get("assignee_id"),
                "updated_at": updated_task.get("updated_at")
            }
        }
        
        return build_response(200, response_data)
        
    except Exception as e:
        logger.exception("Error assigning task")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 