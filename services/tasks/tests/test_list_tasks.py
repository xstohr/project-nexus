"""Tests for the list_tasks Lambda function."""

import json
from unittest.mock import patch
import pytest
from boto3.dynamodb.conditions import Key
from ..functions.task_operations.list_tasks.list_tasks import handler


def create_multiple_tasks(tasks_table, workspace_id="test-workspace-123", count=5):
    """Helper function to create multiple tasks with different statuses."""
    import uuid
    from datetime import datetime
    
    statuses = ["BACKLOG", "TODO", "IN_PROGRESS", "DONE"]
    priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    
    tasks = []
    
    for i in range(count):
        task_id = f"task-{uuid.uuid4()}"
        status = statuses[i % len(statuses)]
        priority = priorities[i % len(priorities)]
        
        task = {
            "PK": f"WORKSPACE#{workspace_id}",
            "SK": f"TASK#{task_id}",
            "task_id": task_id,
            "title": f"Test Task {i+1}",
            "description": f"This is test task {i+1}",
            "workspace_id": workspace_id,
            "account_id": "test-account-123",
            "status": status,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "entity_type": "TASK",
            "created_by": {
                "user_id": "user-123",
                "email": "user@example.com"
            },
            "GSI1PK": f"WORKSPACE#{workspace_id}",
            "GSI1SK": f"STATUS#{status}#PRIORITY#{priority}#TASK#{task_id}"
        }
        
        # Add assignee to some tasks
        if i % 2 == 0:
            assignee_id = f"user-{i+100}"
            task["assignee_id"] = assignee_id
            task["GSI2PK"] = f"WORKSPACE#{workspace_id}"
            task["GSI2SK"] = f"ASSIGNEE#{assignee_id}#TASK#{task_id}"
        
        # Add tags to some tasks
        if i % 3 == 0:
            task["tags"] = [f"tag-{i}", "test"]
        
        # Add due date to some tasks
        if i % 2 == 1:
            task["due_date"] = f"2023-{(i % 12) + 1:02d}-15"
        
        tasks_table.put_item(Item=task)
        tasks.append(task)
    
    return tasks


def test_list_tasks_all(list_tasks_event, tasks_table, accounts_table):
    """Test listing all tasks for a workspace."""
    # Create multiple tasks
    tasks = create_multiple_tasks(tasks_table)
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify response structure
    assert "tasks" in body
    assert "count" in body
    assert "workspace_id" in body
    assert body["workspace_id"] == "test-workspace-123"
    
    # In our test data, we should have tasks with status BACKLOG as per the query param
    backlog_tasks = [t for t in tasks if t["status"] == "BACKLOG"]
    assert body["count"] == len(backlog_tasks)
    
    # Verify each task has the expected status
    for task in body["tasks"]:
        assert task["status"] == "BACKLOG"


def test_list_tasks_by_assignee(list_tasks_event, tasks_table, accounts_table):
    """Test listing tasks by assignee."""
    # Create multiple tasks
    tasks = create_multiple_tasks(tasks_table)
    
    # Modify the event to filter by assignee
    list_tasks_event["queryStringParameters"] = {"assignee_id": "user-100"}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify the results
    assert "tasks" in body
    assert len(body["tasks"]) > 0
    
    # Verify each task has the expected assignee
    for task in body["tasks"]:
        assert task["assignee_id"] == "user-100"


def test_list_tasks_by_priority(list_tasks_event, tasks_table, accounts_table):
    """Test listing tasks by priority."""
    # Create multiple tasks
    tasks = create_multiple_tasks(tasks_table)
    
    # Modify the event to filter by priority
    list_tasks_event["queryStringParameters"] = {"priority": "HIGH"}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify the results
    assert "tasks" in body
    assert len(body["tasks"]) > 0
    
    # Verify each task has the expected priority
    for task in body["tasks"]:
        assert task["priority"] == "HIGH"


def test_list_tasks_by_tag(list_tasks_event, tasks_table, accounts_table):
    """Test listing tasks by tag."""
    # Create multiple tasks
    tasks = create_multiple_tasks(tasks_table)
    
    # Modify the event to filter by tag
    list_tasks_event["queryStringParameters"] = {"tag": "tag-0"}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify the results
    assert "tasks" in body
    assert len(body["tasks"]) > 0
    
    # Verify each task has the expected tag
    for task in body["tasks"]:
        assert "tags" in task
        assert "tag-0" in task["tags"]


def test_list_tasks_with_pagination(list_tasks_event, tasks_table, accounts_table):
    """Test task listing with pagination."""
    # Create many tasks to trigger pagination
    tasks = create_multiple_tasks(tasks_table, count=25)
    
    # Set a small page size
    list_tasks_event["queryStringParameters"] = {"limit": "5"}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    
    # Verify pagination token is present
    assert "next_token" in body
    assert body["count"] <= 5
    
    # Use the pagination token to get the next page
    next_token = body["next_token"]
    list_tasks_event["queryStringParameters"]["next_token"] = next_token
    
    # Call the handler again to get the next page
    response = handler(list_tasks_event, {})
    
    # Parse the response
    assert response["statusCode"] == 200
    body2 = json.loads(response["body"])
    
    # Verify we got different results
    assert body2["tasks"] != body["tasks"]


def test_list_tasks_missing_workspace_id(list_tasks_event):
    """Test task listing with missing workspace ID."""
    # Remove the workspaceId from path parameters
    list_tasks_event["pathParameters"] = {}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert "Missing workspace ID" in body["message"]


def test_list_tasks_unauthorized(list_tasks_event):
    """Test task listing when user is not authenticated."""
    # Remove the user information from the event
    list_tasks_event["requestContext"] = {}
    
    # Call the handler
    response = handler(list_tasks_event, {})
    
    # Verify the error response
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "message" in body
    assert "Unauthorized" in body["message"]


def test_list_tasks_no_workspace_access(list_tasks_event):
    """Test task listing when user has no access to the workspace."""
    # Mock the workspace access check to return False
    with patch("functions.task_operations.list_tasks.list_tasks.validate_workspace_access", 
              return_value=(False, "User does not have access to this workspace")):
        
        # Call the handler
        response = handler(list_tasks_event, {})
        
        # Verify the error response
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "message" in body
        assert "Access denied" in body["message"] 