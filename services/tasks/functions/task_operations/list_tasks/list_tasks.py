"""Lambda function to list tasks for a workspace."""

import json
import os
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools import Logger
from ...shared.utils.utils import build_response, get_user_from_event, validate_workspace_access, DecimalEncoder

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
    """Handle list tasks request."""
    logger.info("List tasks request received")
    
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
        
        # Validate workspace access
        has_access, access_error = validate_workspace_access(user["account_id"], workspace_id)
        if not has_access:
            return build_response(403, {"message": access_error or "Access denied to workspace"})
        
        # Extract query parameters for filtering
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Initialize query parameters
        filter_expression = None
        expression_attr_values = {}
        expression_attr_names = {}
        
        # Set up base query to get all tasks for a workspace
        query_args = {
            'IndexName': 'GSI1',
            'KeyConditionExpression': Key('GSI1PK').eq(f"WORKSPACE#{workspace_id}")
        }
        
        # Add filters based on query parameters
        filter_conditions = []
        
        # Filter by status
        if 'status' in query_params:
            status = query_params['status'].upper()
            valid_statuses = ["BACKLOG", "TODO", "IN_PROGRESS", "DONE"]
            
            if status in valid_statuses:
                # For status, we can optimize by starting the key condition with the status prefix
                query_args['KeyConditionExpression'] = Key('GSI1PK').eq(f"WORKSPACE#{workspace_id}") & \
                                                    Key('GSI1SK').begins_with(f"STATUS#{status}")
        
        # Filter by assignee
        if 'assignee_id' in query_params and query_params['assignee_id']:
            assignee_id = query_params['assignee_id']
            
            # Use GSI2 when filtering by assignee for more efficient queries
            query_args = {
                'IndexName': 'GSI2',
                'KeyConditionExpression': Key('GSI2PK').eq(f"WORKSPACE#{workspace_id}") & \
                                        Key('GSI2SK').begins_with(f"ASSIGNEE#{assignee_id}")
            }
        
        # Filter by priority
        if 'priority' in query_params:
            priority = query_params['priority'].upper()
            valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
            
            if priority in valid_priorities:
                filter_conditions.append("contains(#GSI1SK, :priority)")
                expression_attr_names["#GSI1SK"] = "GSI1SK"
                expression_attr_values[":priority"] = f"PRIORITY#{priority}"
        
        # Filter by tags (if present)
        if 'tag' in query_params:
            tag = query_params['tag']
            filter_conditions.append("contains(#tags, :tag)")
            expression_attr_names["#tags"] = "tags"
            expression_attr_values[":tag"] = tag
        
        # Filter by due date range
        if 'due_date_start' in query_params:
            filter_conditions.append("#due_date >= :due_date_start")
            expression_attr_names["#due_date"] = "due_date"
            expression_attr_values[":due_date_start"] = query_params['due_date_start']
            
        if 'due_date_end' in query_params:
            filter_conditions.append("#due_date <= :due_date_end")
            expression_attr_names["#due_date"] = "due_date"
            expression_attr_values[":due_date_end"] = query_params['due_date_end']
        
        # Combine filter conditions if any exist
        if filter_conditions:
            query_args['FilterExpression'] = " AND ".join(filter_conditions)
            query_args['ExpressionAttributeNames'] = expression_attr_names
            query_args['ExpressionAttributeValues'] = expression_attr_values
        
        # Get pagination token if provided
        if 'next_token' in query_params:
            try:
                exclusive_start_key = json.loads(query_params['next_token'])
                query_args['ExclusiveStartKey'] = exclusive_start_key
            except (json.JSONDecodeError, TypeError):
                return build_response(400, {"message": "Invalid pagination token"})
        
        # Set the page size
        page_size = 20  # Default page size
        if 'limit' in query_params:
            try:
                page_size = int(query_params['limit'])
                if page_size < 1 or page_size > 100:
                    page_size = 20  # Reset to default if out of bounds
            except ValueError:
                pass  # Use default if conversion fails
        
        query_args['Limit'] = page_size
        
        # Execute the query
        response = tasks_table.query(**query_args)
        
        # Process the results
        tasks = response.get('Items', [])
        
        # Format response
        response_data = {
            "tasks": tasks,
            "count": len(tasks),
            "workspace_id": workspace_id
        }
        
        # Add pagination token if more results exist
        if 'LastEvaluatedKey' in response:
            response_data["next_token"] = json.dumps(
                response['LastEvaluatedKey'],
                cls=DecimalEncoder
            )
        
        return build_response(200, response_data)
        
    except Exception as e:
        logger.exception("Error listing tasks")
        return build_response(500, {"message": f"Internal server error: {str(e)}"}) 