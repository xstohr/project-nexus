"""Test fixtures for the Tasks service."""

import os
import json
import uuid
import pytest
import boto3
from moto import mock_dynamodb

# Set environment variables for tests
os.environ["TASKS_TABLE"] = "TasksTable-Test"
os.environ["ACCOUNTS_TABLE"] = "AccountsTable-Test"

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create a mocked DynamoDB client."""
    with mock_dynamodb():
        yield boto3.client("dynamodb", region_name="us-east-1")


@pytest.fixture
def dynamodb_resource(aws_credentials):
    """Create a mocked DynamoDB resource."""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture
def tasks_table(dynamodb_resource):
    """Create a mocked Tasks table."""
    table = dynamodb_resource.create_table(
        TableName=os.environ["TASKS_TABLE"],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Wait until the table exists
    table.meta.client.get_waiter("table_exists").wait(TableName=os.environ["TASKS_TABLE"])
    return table


@pytest.fixture
def accounts_table(dynamodb_resource):
    """Create a mocked Accounts table with workspace data."""
    table = dynamodb_resource.create_table(
        TableName=os.environ["ACCOUNTS_TABLE"],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Wait until the table exists
    table.meta.client.get_waiter("table_exists").wait(TableName=os.environ["ACCOUNTS_TABLE"])
    
    # Add test account and workspace records
    account_id = "test-account-123"
    workspace_id = "test-workspace-123"
    
    # Create account record
    table.put_item(
        Item={
            "PK": f"ACCOUNT#{account_id}",
            "SK": "METADATA",
            "account_id": account_id,
            "name": "Test Account",
            "email": "test@example.com",
            "status": "ACTIVE",
            "created_at": "2023-01-01T00:00:00Z",
            "entity_type": "ACCOUNT"
        }
    )
    
    # Create workspace record
    table.put_item(
        Item={
            "PK": f"ACCOUNT#{account_id}",
            "SK": f"WORKSPACE#{workspace_id}",
            "workspace_id": workspace_id,
            "account_id": account_id,
            "name": "Test Workspace",
            "description": "Test Workspace Description",
            "status": "ACTIVE",
            "created_at": "2023-01-01T00:00:00Z",
            "entity_type": "WORKSPACE"
        }
    )
    
    return table


@pytest.fixture
def sample_task():
    """Return a sample task item for testing."""
    account_id = "test-account-123"
    workspace_id = "test-workspace-123"
    task_id = f"task-{uuid.uuid4()}"
    timestamp = "2023-01-02T00:00:00Z"
    
    return {
        "PK": f"WORKSPACE#{workspace_id}",
        "SK": f"TASK#{task_id}",
        "task_id": task_id,
        "title": "Test Task",
        "description": "This is a test task",
        "workspace_id": workspace_id,
        "account_id": account_id,
        "status": "BACKLOG",
        "priority": "MEDIUM",
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_by": {
            "user_id": "user-123",
            "email": "user@example.com"
        },
        "due_date": "2023-02-01",
        "assignee_id": "user-456",
        "tags": ["test", "sample"],
        "entity_type": "TASK",
        "GSI1PK": f"WORKSPACE#{workspace_id}",
        "GSI1SK": f"STATUS#BACKLOG#PRIORITY#MEDIUM#TASK#{task_id}",
        "GSI2PK": f"WORKSPACE#{workspace_id}",
        "GSI2SK": f"ASSIGNEE#user-456#TASK#{task_id}"
    }


@pytest.fixture
def populated_tasks_table(tasks_table, sample_task):
    """Populate the tasks table with a sample task."""
    tasks_table.put_item(Item=sample_task)
    return tasks_table


@pytest.fixture
def api_gateway_event_template():
    """Return a template for API Gateway event."""
    return {
        "httpMethod": "GET",
        "path": "/workspaces/test-workspace-123/tasks",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"
        },
        "pathParameters": {
            "workspaceId": "test-workspace-123"
        },
        "queryStringParameters": None,
        "body": None,
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "email": "user@example.com",
                    "custom:account_id": "test-account-123"
                }
            }
        }
    }


@pytest.fixture
def create_task_event(api_gateway_event_template):
    """Create an event for creating a task."""
    event = api_gateway_event_template.copy()
    event["httpMethod"] = "POST"
    event["body"] = json.dumps({
        "title": "New Test Task",
        "description": "This is a new test task created via API",
        "status": "TODO",
        "priority": "HIGH",
        "due_date": "2023-03-01",
        "assignee_id": "user-789",
        "tags": ["api", "test"]
    })
    return event


@pytest.fixture
def get_task_event(api_gateway_event_template, sample_task):
    """Create an event for getting a task."""
    event = api_gateway_event_template.copy()
    event["httpMethod"] = "GET"
    event["path"] = f"/workspaces/test-workspace-123/tasks/{sample_task['task_id']}"
    event["pathParameters"] = {
        "workspaceId": "test-workspace-123",
        "taskId": sample_task["task_id"]
    }
    return event


@pytest.fixture
def update_task_event(api_gateway_event_template, sample_task):
    """Create an event for updating a task."""
    event = api_gateway_event_template.copy()
    event["httpMethod"] = "PUT"
    event["path"] = f"/workspaces/test-workspace-123/tasks/{sample_task['task_id']}"
    event["pathParameters"] = {
        "workspaceId": "test-workspace-123",
        "taskId": sample_task["task_id"]
    }
    event["body"] = json.dumps({
        "title": "Updated Task Title",
        "status": "IN_PROGRESS",
        "priority": "URGENT"
    })
    return event


@pytest.fixture
def delete_task_event(api_gateway_event_template, sample_task):
    """Create an event for deleting a task."""
    event = api_gateway_event_template.copy()
    event["httpMethod"] = "DELETE"
    event["path"] = f"/workspaces/test-workspace-123/tasks/{sample_task['task_id']}"
    event["pathParameters"] = {
        "workspaceId": "test-workspace-123",
        "taskId": sample_task["task_id"]
    }
    return event


@pytest.fixture
def list_tasks_event(api_gateway_event_template):
    """Create an event for listing tasks."""
    event = api_gateway_event_template.copy()
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "status": "BACKLOG",
        "limit": "10"
    }
    return event 