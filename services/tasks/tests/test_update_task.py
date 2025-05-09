"""Tests for the update_task Lambda function."""

import json
from unittest.mock import patch
import pytest
from ..functions.task_operations.update_task.update_task import handler


def test_update_task_success(update_task_event, populated_tasks_table, sample_task):
    """Test successful task update."""
    # Call the handler with the update task event
    response = handler(update_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "message" in body
    assert "task" in body
    assert body["message"] == "Task updated successfully"
    
    # Verify task properties were updated
    task = body["task"]
    assert task["task_id"] == sample_task["task_id"]
    assert task["title"] == "Updated Task Title"  # Updated value
    assert task["status"] == "IN_PROGRESS"  # Updated value
    assert task["priority"] == "URGENT"  # Updated value
    
    # Verify unchanged values
    assert task["workspace_id"] == sample_task["workspace_id"]
    assert "created_at" in task
    assert "updated_at" in task
    assert task["description"] == sample_task["description"]
    assert task["assignee_id"] == sample_task["assignee_id"]
    assert task["due_date"] == sample_task["due_date"]
    
    # Verify that updated_at is different from the original
    assert task["updated_at"] != sample_task["updated_at"]
    
    # Verify the task was actually updated in DynamoDB
    response = populated_tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#{sample_task['workspace_id']}",
            "SK": f"TASK#{sample_task['task_id']}"
        }
    )
    
    assert "Item" in response
    saved_task = response["Item"]
    assert saved_task["title"] == "Updated Task Title"
    assert saved_task["status"] == "IN_PROGRESS"
    assert saved_task["priority"] == "URGENT"
    
    # Verify indexes were updated
    assert saved_task["GSI1SK"].startswith("STATUS#IN_PROGRESS#PRIORITY#URGENT")


def test_update_task_not_found(update_task_event, tasks_table):
    """Test task update when task doesn't exist."""
    # Modify the event to use a non-existent task ID
    update_task_event["pathParameters"]["taskId"] = "non-existent-task-id"
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "message" in body
    assert "not found" in body["message"]


def test_update_task_invalid_status(update_task_event, populated_tasks_table):
    """Test task update with invalid status."""
    # Modify the event to have an invalid status
    event_body = json.loads(update_task_event["body"])
    event_body["status"] = "INVALID_STATUS"
    update_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Invalid status value" in body["message"]


def test_update_task_invalid_priority(update_task_event, populated_tasks_table):
    """Test task update with invalid priority."""
    # Modify the event to have an invalid priority
    event_body = json.loads(update_task_event["body"])
    event_body["priority"] = "INVALID_PRIORITY"
    update_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Invalid priority value" in body["message"]


def test_update_task_invalid_tags(update_task_event, populated_tasks_table):
    """Test task update with invalid tags format."""
    # Modify the event to have tags as a string instead of an array
    event_body = json.loads(update_task_event["body"])
    event_body["tags"] = "not-an-array"
    update_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Tags must be an array" in body["message"]


def test_update_task_missing_task_id(update_task_event, populated_tasks_table):
    """Test task update with missing task ID."""
    # Remove the taskId from path parameters
    update_task_event["pathParameters"].pop("taskId")
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing task ID" in body["message"]


def test_update_task_change_assignee(update_task_event, populated_tasks_table, sample_task):
    """Test updating task assignee."""
    # Modify the event to change the assignee
    event_body = json.loads(update_task_event["body"])
    event_body["assignee_id"] = "new-assignee-id"
    update_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify task properties were updated
    task = body["task"]
    assert task["assignee_id"] == "new-assignee-id"
    
    # Verify the task was actually updated in DynamoDB
    response = populated_tasks_table.get_item(
        Key={
            "PK": f"WORKSPACE#{sample_task['workspace_id']}",
            "SK": f"TASK#{sample_task['task_id']}"
        }
    )
    
    assert "Item" in response
    saved_task = response["Item"]
    assert saved_task["assignee_id"] == "new-assignee-id"
    
    # Verify GSI2 was updated
    assert saved_task["GSI2SK"].startswith("ASSIGNEE#new-assignee-id")


def test_update_task_remove_assignee(update_task_event, populated_tasks_table, sample_task):
    """Test removing assignee from task."""
    # Modify the event to remove the assignee
    event_body = json.loads(update_task_event["body"])
    event_body["assignee_id"] = ""
    update_task_event["body"] = json.dumps(event_body)
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
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


def test_update_task_unauthorized(update_task_event):
    """Test task update when user is not authenticated."""
    # Remove the user information from the event
    update_task_event["requestContext"] = {}
    
    # Call the handler
    response = handler(update_task_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_update_task_no_workspace_access(update_task_event):
    """Test task update when user has no access to the workspace."""
    # Mock the workspace access check to return False
    with patch("functions.task_operations.update_task.update_task.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(update_task_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"] 