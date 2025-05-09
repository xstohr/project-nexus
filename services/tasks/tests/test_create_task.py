"""Tests for the create_task Lambda function."""

import json
from unittest.mock import patch
import pytest
from ..functions.task_operations.create_task.create_task import handler


def test_create_task_success(create_task_event, tasks_table, accounts_table):
    """Test successful task creation."""
    # Call the handler with the create task event
    response = handler(create_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "message" in body
    assert "task" in body
    assert body["message"] == "Task created successfully"
    
    # Verify task properties
    task = body["task"]
    assert "task_id" in task
    assert task["title"] == "New Test Task"
    assert task["workspace_id"] == "test-workspace-123"
    assert task["status"] == "TODO"
    assert task["priority"] == "HIGH"
    assert "created_at" in task
    assert "updated_at" in task
    assert task["description"] == "This is a new test task created via API"
    assert task["assignee_id"] == "user-789"
    assert task["due_date"] == "2023-03-01"
    assert "api" in task["tags"]
    assert "test" in task["tags"]
    
    # Verify the task was actually saved to DynamoDB
    response = tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#test-workspace-123",
            "SK": f"TASK#{task['task_id']}"
        }
    )
    
    assert "Item" in response
    saved_task = response["Item"]
    assert saved_task["title"] == "New Test Task"
    assert saved_task["status"] == "TODO"
    assert saved_task["priority"] == "HIGH"
    assert saved_task["GSI1SK"].startswith("STATUS#TODO#PRIORITY#HIGH")
    assert saved_task["GSI2SK"].startswith("ASSIGNEE#user-789")


def test_create_task_missing_title(create_task_event, tasks_table):
    """Test task creation with missing required field."""
    # Modify the event to have an empty title
    event_body = json.loads(create_task_event["body"])
    event_body.pop("title")
    create_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing required field: title" in body["message"]


def test_create_task_invalid_status(create_task_event, tasks_table):
    """Test task creation with invalid status."""
    # Modify the event to have an invalid status
    event_body = json.loads(create_task_event["body"])
    event_body["status"] = "INVALID_STATUS"
    create_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Invalid status value" in body["message"]


def test_create_task_invalid_priority(create_task_event, tasks_table):
    """Test task creation with invalid priority."""
    # Modify the event to have an invalid priority
    event_body = json.loads(create_task_event["body"])
    event_body["priority"] = "INVALID_PRIORITY"
    create_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Invalid priority value" in body["message"]


def test_create_task_invalid_tags(create_task_event, tasks_table):
    """Test task creation with invalid tags format."""
    # Modify the event to have tags as a string instead of an array
    event_body = json.loads(create_task_event["body"])
    event_body["tags"] = "not-an-array"
    create_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Tags must be an array" in body["message"]


def test_create_task_missing_workspace_id(create_task_event, tasks_table):
    """Test task creation with missing workspace ID."""
    # Remove the workspaceId from path parameters
    create_task_event["pathParameters"] = {}
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing workspace ID" in body["message"]


def test_create_task_unauthorized(create_task_event, tasks_table):
    """Test task creation when user is not authenticated."""
    # Remove the user information from the event
    create_task_event["requestContext"] = {}
    
    # Call the handler
    response = handler(create_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_create_task_no_workspace_access(create_task_event, tasks_table):
    """Test task creation when user has no access to the workspace."""
    # Mock the workspace access check to return False
    with patch("functions.task_operations.create_task.create_task.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(create_task_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"] 