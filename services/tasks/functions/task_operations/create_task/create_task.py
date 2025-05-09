"""Lambda function to create a new task in a workspace."""

import json
import os
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, validate_workspace_access
from ...shared.models.task_models import create_task_item, validate_task_input

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
    """Handle task creation request."""
    logger.info("Create task request received")
    
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
        
        # Extract the workspace_id from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'workspaceId' not in event['pathParameters']:
            return build_response(400, {"message": "Missing workspace ID"})
        workspace_id = event['pathParameters']['workspaceId']
        
        # Validate workspace access
        has_access, access_error = validate_workspace_access(user["account_id"], workspace_id)
        if not has_access:
            return build_response(403, {"message": access_error or "Access denied to workspace"})
        
        # Validate task data
        is_valid, validation_error = validate_task_input(body)
        if not is_valid:
            return build_response(400, {"message": validation_error})
        
        # Create the task item for DynamoDB
        task_item = create_task_item(
            workspace_id=workspace_id,
            account_id=user["account_id"],
            title=body.get("title"),
            description=body.get("description"),
            status=body.get("status", "BACKLOG"),
            priority=body.get("priority", "MEDIUM"),
            assignee_id=body.get("assignee_id"),
            creator_id=user["user_id"],
            creator_email=user["email"],
            due_date=body.get("due_date"),
            tags=body.get("tags")
        )
        
        # Save the task to DynamoDB
        tasks_table.put_item(Item=task_item)
        
        # Prepare the response
        response_data = {
            "message": "Task created successfully",
            "task": {
                "task_id": task_item["task_id"],
                "title": task_item["title"],
                "workspace_id": task_item["workspace_id"],
                "status": task_item["status"],
                "priority": task_item["priority"],
                "created_at": task_item["created_at"],
                "updated_at": task_item["updated_at"],
            }
        }
        
        # Add optional fields to response if they exist
        if "description" in task_item:
            response_data["task"]["description"] = task_item["description"]
        
        if "assignee_id" in task_item:
            response_data["task"]["assignee_id"] = task_item["assignee_id"]
        
        if "due_date" in task_item:
            response_data["task"]["due_date"] = task_item["due_date"]
        
        if "tags" in task_item:
            response_data["task"]["tags"] = task_item["tags"]
        
        return build_response(201, response_data)
        
    except Exception as e:
        logger.exception("Error creating task")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 