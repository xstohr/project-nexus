"""Common utilities for Tasks Service Lambda functions."""

import json
import os
import boto3
from aws_lambda_powertools import Logger
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Initialize shared resources
logger = Logger()
dynamodb = boto3.resource("dynamodb")

# Environment variables
TASKS_TABLE = os.environ.get("TASKS_TABLE")
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE")

# Initialize DynamoDB tables
tasks_table = dynamodb.Table(TASKS_TABLE)
accounts_table = dynamodb.Table(ACCOUNTS_TABLE) if ACCOUNTS_TABLE else None

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal objects from DynamoDB to numbers."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 else int(o)
        return super(DecimalEncoder, self).default(o)

def get_user_from_event(event):
    """Extract the authenticated user from event context."""
    # In a production environment, this would come from a JWT token or Cognito claims
    # For development, we'll extract from headers or use a default
    auth_header = event.get("headers", {}).get("Authorization", "")
    
    # Extract user info (simplified for now)
    # In production, this would properly decode and validate the JWT
    if auth_header.startswith("Bearer "):
        # Simulate extracting user from token
        return {
            "user_id": "test-user-id",  # Would come from token
            "email": "test@example.com",  # Would come from token
            "tenant_id": "test-tenant-id"  # Would come from token
        }
    
    # Default for testing
    return {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "tenant_id": "test-tenant-id"
    }

def build_response(status_code, body):
    """Build a standard API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        }
    }

def get_task_by_id(task_id):
    """Get task details by ID."""
    try:
        response = tasks_table.query(
            IndexName="TaskIdIndex",
            KeyConditionExpression=Key("task_id").eq(task_id)
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error retrieving task: {str(e)}")
        return None

def get_workspace_by_id(workspace_id):
    """Get workspace details by ID."""
    if not accounts_table:
        logger.warning("ACCOUNTS_TABLE not configured, skipping workspace validation")
        return {"workspace_id": workspace_id, "status": "ACTIVE"}
        
    try:
        response = accounts_table.query(
            IndexName="WorkspaceIdIndex",
            KeyConditionExpression=Key("workspace_id").eq(workspace_id)
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error retrieving workspace: {str(e)}")
        return None

def validate_workspace_access(workspace_id, user_id):
    """Validate a user has access to a workspace."""
    # This is a simplified validation that would need to be expanded
    # In production, we'd check if the user has appropriate roles/permissions
    if not accounts_table:
        logger.warning("ACCOUNTS_TABLE not configured, skipping access validation")
        return True
        
    try:
        # Check if user has a role in this workspace
        response = accounts_table.query(
            KeyConditionExpression=Key("PK").eq(f"WORKSPACE#{workspace_id}") & 
                                  Key("SK").eq(f"USER#{user_id}")
        )
        
        return len(response.get("Items", [])) > 0
    except Exception as e:
        logger.error(f"Error validating workspace access: {str(e)}")
        return False 