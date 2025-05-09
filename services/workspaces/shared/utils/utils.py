"""Common utilities for Workspace Service Lambda functions."""

import json
import os
import boto3
from aws_lambda_powertools import Logger

# Initialize shared resources
logger = Logger()
dynamodb = boto3.resource("dynamodb")

# Environment variables
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE")

# Initialize DynamoDB table
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)

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
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        }
    }

def get_workspace_by_id(workspace_id):
    """Get workspace details by ID."""
    try:
        response = accounts_table.query(
            IndexName="WorkspaceIdIndex",
            KeyConditionExpression="workspace_id = :workspace_id",
            ExpressionAttributeValues={
                ":workspace_id": workspace_id
            }
        )
        
        items = response.get("Items", [])
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logger.error(f"Error retrieving workspace: {str(e)}")
        return None 