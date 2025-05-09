"""Tests for the assign_task Lambda function."""

import json
from unittest.mock import patch
import pytest
from ..functions.task_operations.assign_task.assign_task import handler


def test_assign_task_success(get_task_event, populated_tasks_table, sample_task):
    """Test successful task assignment."""
    # Modify the event to be for assignment
    get_task_event["body"] = json.dumps({"assignee_id": "new-assignee-123"})
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "message" in body
    assert "task" in body
    assert body["message"] == "Task assignment updated successfully"
    
    # Verify task properties were updated
    task = body["task"]
    assert task["task_id"] == sample_task["task_id"]
    assert task["assignee_id"] == "new-assignee-123"
    
    # Verify the task was actually updated in DynamoDB
    response = populated_tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#{sample_task['workspace_id']}",
            "SK": f"TASK#{sample_task['task_id']}"
        }
    )
    
    assert "Item" in response
    saved_task = response["Item"]
    assert saved_task["assignee_id"] == "new-assignee-123"
    
    # Verify GSI2 was updated
    assert saved_task["GSI2PK"] == f"WORKSPACE#{sample_task['workspace_id']}"
    assert saved_task["GSI2SK"].startswith(f"ASSIGNEE#new-assignee-123#TASK#{sample_task['task_id']}")


def test_remove_assignee(get_task_event, populated_tasks_table, sample_task):
    """Test removing assignee from task."""
    # Modify the event to be for removing assignee
    get_task_event["body"] = json.dumps({"assignee_id": ""})
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "message" in body
    assert "task" in body
    
    # Verify task properties were updated
    task = body["task"]
    assert task["assignee_id"] == ""
    
    # Verify the task was actually updated in DynamoDB
    response = populated_tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#{sample_task['workspace_id']}",
            "SK": f"TASK#{sample_task['task_id']}"
        }
    )
    
    assert "Item" in response
    saved_task = response["Item"]
    assert saved_task["assignee_id"] == ""
    
    # GSI2 indices should be removed
    assert "GSI2PK" not in saved_task
    assert "GSI2SK" not in saved_task


def test_assign_task_missing_body(get_task_event):
    """Test assignment with missing body."""
    # Remove the body
    get_task_event.pop("body", None)
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing request body" in body["message"]


def test_assign_task_missing_assignee_id(get_task_event):
    """Test assignment with missing assignee_id in body."""
    # Set body with missing assignee_id
    get_task_event["body"] = json.dumps({"other_field": "value"})
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing assignee_id" in body["message"]


def test_assign_task_not_found(get_task_event, tasks_table):
    """Test assignment when task doesn't exist."""
    # Modify the event to use non-existent task ID
    get_task_event["pathParameters"]["taskId"] = "non-existent-task-id"
    get_task_event["body"] = json.dumps({"assignee_id": "assignee-123"})
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "message" in body
    assert "not found" in body["message"]


def test_assign_task_unauthorized(get_task_event):
    """Test assignment when user is not authenticated."""
    # Remove the user information
    get_task_event["requestContext"] = {}
    get_task_event["body"] = json.dumps({"assignee_id": "assignee-123"})
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_assign_task_no_workspace_access(get_task_event):
    """Test assignment when user has no access to workspace."""
    # Set body with assignee_id
    get_task_event["body"] = json.dumps({"assignee_id": "assignee-123"})
    
    # Mock the workspace access check to return False
    with patch("functions.task_operations.assign_task.assign_task.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(get_task_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"] 