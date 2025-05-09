"""Common utilities for Account Service Lambda functions."""

import json
import os
import boto3
from aws_lambda_powertools import Logger

# Initialize shared resources
logger = Logger()
dynamodb = boto3.resource("dynamodb")

# Environment variables
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE")
USER_POOL_ID = os.environ.get("USER_POOL_ID")

# Constants
USER_ROLES = {
    "ADMIN": "Administrator with full system access",
    "SUPER_USER": "Power user with workspace-level administration",
    "BASIC_USER": "Regular user with limited permissions"
}

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

def generate_pk_sk(entity_type, entity_id, subtype=None):
    """Generate primary key and sort key for DynamoDB."""
    pk = f"{entity_type}#{entity_id}"
    sk = "METADATA" if subtype is None else f"{subtype}"
    return pk, sk

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

def validate_role(role):
    """Validate if a role is valid."""
    if not role or role not in USER_ROLES:
        valid_roles = ", ".join(USER_ROLES.keys())
        return False, f"Invalid role. Must be one of: {valid_roles}"
    return True, None 