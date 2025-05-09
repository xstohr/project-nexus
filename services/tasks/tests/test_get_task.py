"""Tests for the get_task Lambda function."""

import json
from unittest.mock import patch
import pytest
from ..functions.task_operations.get_task.get_task import handler


def test_get_task_success(get_task_event, populated_tasks_table, sample_task):
    """Test successful task retrieval."""
    # Call the handler with the get task event
    response = handler(get_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "task" in body
    
    # Verify task properties
    task = body["task"]
    assert task["task_id"] == sample_task["task_id"]
    assert task["title"] == sample_task["title"]
    assert task["workspace_id"] == sample_task["workspace_id"]
    assert task["status"] == sample_task["status"]
    assert task["priority"] == sample_task["priority"]
    assert task["created_at"] == sample_task["created_at"]
    assert task["updated_at"] == sample_task["updated_at"]
    assert task["description"] == sample_task["description"]
    assert task["assignee_id"] == sample_task["assignee_id"]
    assert task["due_date"] == sample_task["due_date"]
    assert task["tags"] == sample_task["tags"]


def test_get_task_not_found(get_task_event, tasks_table):
    """Test task retrieval when task doesn't exist."""
    # Modify the event to use a non-existent task ID
    get_task_event["pathParameters"]["taskId"] = "non-existent-task-id"
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "message" in body
    assert "not found" in body["message"]


def test_get_task_missing_task_id(get_task_event):
    """Test task retrieval with missing task ID."""
    # Remove the taskId from path parameters
    get_task_event["pathParameters"].pop("taskId")
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing task ID" in body["message"]


def test_get_task_missing_workspace_id(get_task_event):
    """Test task retrieval with missing workspace ID."""
    # Remove the workspaceId from path parameters
    get_task_event["pathParameters"].pop("workspaceId")
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing workspace ID" in body["message"]


def test_get_task_unauthorized(get_task_event):
    """Test task retrieval when user is not authenticated."""
    # Remove the user information from the event
    get_task_event["requestContext"] = {}
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_get_task_no_workspace_access(get_task_event):
    """Test task retrieval when user has no access to the workspace."""
    # Mock the workspace access check to return False
    with patch("functions.task_operations.get_task.get_task.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(get_task_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"]


def test_get_task_wrong_workspace(get_task_event, populated_tasks_table, sample_task):
    """Test task retrieval with the wrong workspace ID."""
    # Modify the event to use a different workspace ID
    get_task_event["pathParameters"]["workspaceId"] = "different-workspace-id"
    
    # Call the handler
    response = handler(get_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "message" in body
    assert "not found in workspace" in body["message"] 