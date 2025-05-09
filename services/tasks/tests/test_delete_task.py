"""Tests for the delete_task Lambda function."""

import json
from unittest.mock import patch
import pytest
from ..functions.task_operations.delete_task.delete_task import handler


def test_delete_task_success(delete_task_event, populated_tasks_table, sample_task):
    """Test successful task deletion."""
    # Call the handler with the delete task event
    response = handler(delete_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "message" in body
    assert "task_id" in body
    assert "workspace_id" in body
    assert body["message"] == "Task deleted successfully"
    assert body["task_id"] == sample_task["task_id"]
    assert body["workspace_id"] == sample_task["workspace_id"]
    
    # Verify the task was actually deleted from DynamoDB
    response = populated_tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#{sample_task['workspace_id']}",
            "SK": f"TASK#{sample_task['task_id']}"
        }
    )
    
    # Should not have an Item in the response if deleted
    assert "Item" not in response


def test_delete_task_not_found(delete_task_event, tasks_table):
    """Test task deletion when task doesn't exist."""
    # Modify the event to use a non-existent task ID
    delete_task_event["pathParameters"]["taskId"] = "non-existent-task-id"
    
    # Call the handler
    response = handler(delete_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "message" in body
    assert "not found" in body["message"]


def test_delete_task_missing_task_id(delete_task_event):
    """Test task deletion with missing task ID."""
    # Remove the taskId from path parameters
    delete_task_event["pathParameters"].pop("taskId")
    
    # Call the handler
    response = handler(delete_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing task ID" in body["message"]


def test_delete_task_missing_workspace_id(delete_task_event):
    """Test task deletion with missing workspace ID."""
    # Remove the workspaceId from path parameters
    delete_task_event["pathParameters"].pop("workspaceId")
    
    # Call the handler
    response = handler(delete_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing workspace ID" in body["message"]


def test_delete_task_unauthorized(delete_task_event):
    """Test task deletion when user is not authenticated."""
    # Remove the user information from the event
    delete_task_event["requestContext"] = {}
    
    # Call the handler
    response = handler(delete_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_delete_task_no_workspace_access(delete_task_event):
    """Test task deletion when user has no access to the workspace."""
    # Mock the workspace access check to return False
    with patch("functions.task_operations.delete_task.delete_task.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(delete_task_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"] 