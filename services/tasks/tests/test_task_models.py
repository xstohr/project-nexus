"""Tests for the task models module."""

import pytest
from ..functions.shared.models.task_models import (
    generate_id,
    get_timestamp,
    create_task_item,
    validate_task_input,
    prepare_update_expression
)


def test_generate_id():
    """Test ID generation."""
    # Test default prefix
    task_id = generate_id()
    assert task_id.startswith("task-")
    assert len(task_id) > 10  # Should be a reasonably long UUID-based ID
    
    # Test custom prefix
    task_id = generate_id(prefix="custom-")
    assert task_id.startswith("custom-")


def test_get_timestamp():
    """Test timestamp generation."""
    timestamp = get_timestamp()
    assert isinstance(timestamp, str)
    # Basic ISO format validation: YYYY-MM-DDTHH:MM:SS
    assert len(timestamp) >= 19
    assert "T" in timestamp


def test_create_task_item():
    """Test task item creation."""
    # Test with required fields only
    task = create_task_item(
        workspace_id="workspace-123",
        account_id="account-123", 
        title="Test Task"
    )
    
    # Check required fields
    assert "PK" in task
    assert "SK" in task
    assert task["title"] == "Test Task"
    assert task["workspace_id"] == "workspace-123"
    assert task["account_id"] == "account-123"
    assert task["status"] == "BACKLOG"  # Default
    assert task["priority"] == "MEDIUM"  # Default
    assert "created_at" in task
    assert "updated_at" in task
    assert "created_by" in task
    assert "entity_type" in task
    assert task["entity_type"] == "TASK"
    assert "GSI1PK" in task
    assert "GSI1SK" in task
    
    # Check PK and SK format
    assert task["PK"] == f"WORKSPACE#workspace-123"
    assert task["SK"].startswith("TASK#")
    
    # Check GSI1 format
    assert task["GSI1PK"] == f"WORKSPACE#workspace-123"
    assert task["GSI1SK"].startswith("STATUS#BACKLOG#PRIORITY#MEDIUM#TASK#")
    
    # Check optional fields are not present
    assert "description" not in task
    assert "assignee_id" not in task
    assert "GSI2PK" not in task
    assert "GSI2SK" not in task
    assert "due_date" not in task
    assert "tags" not in task
    
    # Test with all fields
    task = create_task_item(
        workspace_id="workspace-123",
        account_id="account-123", 
        title="Test Task",
        description="Task description",
        status="TODO",
        priority="HIGH",
        assignee_id="user-123",
        creator_id="creator-123",
        creator_email="creator@example.com",
        due_date="2023-12-31",
        tags=["test", "important"]
    )
    
    # Check optional fields are present
    assert task["description"] == "Task description"
    assert task["status"] == "TODO"
    assert task["priority"] == "HIGH"
    assert task["assignee_id"] == "user-123"
    assert task["created_by"]["user_id"] == "creator-123"
    assert task["created_by"]["email"] == "creator@example.com"
    assert task["due_date"] == "2023-12-31"
    assert task["tags"] == ["test", "important"]
    
    # Check GSI updates for assignee
    assert task["GSI2PK"] == f"WORKSPACE#workspace-123"
    assert task["GSI2SK"].startswith("ASSIGNEE#user-123#TASK#")
    
    # Check GSI1 changes for status/priority
    assert task["GSI1SK"].startswith("STATUS#TODO#PRIORITY#HIGH#TASK#")


def test_validate_task_input():
    """Test task input validation."""
    # Test valid input
    valid_task = {
        "title": "Valid Task",
        "status": "TODO",
        "priority": "HIGH"
    }
    is_valid, error = validate_task_input(valid_task)
    assert is_valid is True
    assert error is None
    
    # Test missing title
    invalid_task = {
        "status": "TODO",
        "priority": "HIGH"
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "Missing required field: title" in error
    
    # Test empty title
    invalid_task = {
        "title": "",
        "status": "TODO",
        "priority": "HIGH"
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "Missing required field: title" in error
    
    # Test invalid status
    invalid_task = {
        "title": "Valid Task",
        "status": "INVALID_STATUS",
        "priority": "HIGH"
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "Invalid status value" in error
    
    # Test invalid priority
    invalid_task = {
        "title": "Valid Task",
        "status": "TODO",
        "priority": "INVALID_PRIORITY"
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "Invalid priority value" in error
    
    # Test invalid tags (not a list)
    invalid_task = {
        "title": "Valid Task",
        "tags": "not-a-list"
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "Tags must be an array" in error
    
    # Test invalid tags (not all strings)
    invalid_task = {
        "title": "Valid Task",
        "tags": ["valid", 123]
    }
    is_valid, error = validate_task_input(invalid_task)
    assert is_valid is False
    assert "All tags must be strings" in error


def test_prepare_update_expression():
    """Test preparation of update expressions."""
    # Setup a test task
    existing_task = {
        "task_id": "task-123",
        "workspace_id": "workspace-123",
        "status": "BACKLOG",
        "priority": "MEDIUM"
    }
    
    # Test simple field updates
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description",
        "_existing_task": existing_task
    }
    
    update_expr, expr_values, expr_names = prepare_update_expression(update_data)
    
    # Check update expression basics
    assert update_expr.startswith("SET updated_at = :updated_at")
    assert ":updated_at" in expr_values
    
    # Check title and description are in the expression
    assert "#title = :title" in update_expr
    assert "#description = :description" in update_expr
    assert ":title" in expr_values
    assert ":description" in expr_values
    assert expr_values[":title"] == "Updated Title"
    assert expr_values[":description"] == "Updated Description"
    assert "#title" in expr_names
    assert "#description" in expr_names
    assert expr_names["#title"] == "title"
    assert expr_names["#description"] == "description"
    
    # Test status and priority update (affects GSI1SK)
    update_data = {
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "_existing_task": existing_task
    }
    
    update_expr, expr_values, expr_names = prepare_update_expression(update_data)
    
    # Check GSI1SK is updated
    assert "#GSI1SK = :gsi1sk" in update_expr
    assert ":gsi1sk" in expr_values
    assert expr_values[":gsi1sk"].startswith("STATUS#IN_PROGRESS#PRIORITY#HIGH#TASK#task-123")
    assert "#GSI1SK" in expr_names
    assert expr_names["#GSI1SK"] == "GSI1SK"
    
    # Test assignee update (affects GSI2)
    update_data = {
        "assignee_id": "new-assignee",
        "_existing_task": existing_task
    }
    
    update_expr, expr_values, expr_names = prepare_update_expression(update_data)
    
    # Check GSI2 keys are added
    assert "#GSI2PK = :gsi2pk" in update_expr
    assert "#GSI2SK = :gsi2sk" in update_expr
    assert ":gsi2pk" in expr_values
    assert ":gsi2sk" in expr_values
    assert expr_values[":gsi2pk"] == "WORKSPACE#workspace-123"
    assert expr_values[":gsi2sk"].startswith("ASSIGNEE#new-assignee#TASK#task-123")
    assert "#GSI2PK" in expr_names
    assert "#GSI2SK" in expr_names
    assert expr_names["#GSI2PK"] == "GSI2PK"
    assert expr_names["#GSI2SK"] == "GSI2SK"
    
    # Test removing assignee
    update_data = {
        "assignee_id": "",
        "_existing_task": {
            "task_id": "task-123",
            "workspace_id": "workspace-123",
            "status": "BACKLOG",
            "priority": "MEDIUM",
            "GSI2PK": "WORKSPACE#workspace-123",
            "GSI2SK": "ASSIGNEE#old-assignee#TASK#task-123"
        }
    }
    
    update_expr, expr_values, expr_names = prepare_update_expression(update_data)
    
    # Check GSI2 keys are removed
    assert "REMOVE GSI2PK, GSI2SK" in update_expr 