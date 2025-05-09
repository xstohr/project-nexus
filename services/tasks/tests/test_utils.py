"""Tests for the utilities module."""

import json
import decimal
from unittest.mock import patch, MagicMock
import pytest
from ..functions.shared.utils.utils import (
    DecimalEncoder,
    get_user_from_event,
    build_response,
    get_task_by_id,
    validate_workspace_access
)


def test_decimal_encoder():
    """Test the DecimalEncoder."""
    # Create an instance of the encoder
    encoder = DecimalEncoder()
    
    # Test with Decimal
    decimal_value = decimal.Decimal('10.5')
    result = encoder.default(decimal_value)
    assert result == 10.5
    assert isinstance(result, float)
    
    # Test with a set
    set_value = {1, 2, 3}
    result = encoder.default(set_value)
    assert result == [1, 2, 3]
    assert isinstance(result, list)
    
    # Test with a non-handled type
    with pytest.raises(TypeError):
        encoder.default("string")


def test_get_user_from_event():
    """Test extracting user information from event."""
    # Test with valid event from API Gateway authorizer
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-123",
                    "email": "user@example.com",
                    "custom:account_id": "account-123"
                }
            }
        }
    }
    
    user = get_user_from_event(event)
    assert user is not None
    assert user["user_id"] == "user-123"
    assert user["email"] == "user@example.com"
    assert user["account_id"] == "account-123"
    
    # Test with missing request context
    event = {}
    user = get_user_from_event(event)
    assert user is None
    
    # Test with missing authorizer
    event = {"requestContext": {}}
    user = get_user_from_event(event)
    assert user is None
    
    # Test with missing claims
    event = {"requestContext": {"authorizer": {}}}
    user = get_user_from_event(event)
    assert user is None
    
    # Test with dev mode event signature
    event = {
        "headers": {
            "Authorization": "Dev user-123 user@example.com account-123"
        }
    }
    user = get_user_from_event(event)
    assert user is not None
    assert user["user_id"] == "user-123"
    assert user["email"] == "user@example.com"
    assert user["account_id"] == "account-123"


def test_build_response():
    """Test building API responses."""
    # Test simple response
    data = {"message": "Success"}
    response = build_response(200, data)
    
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert response["headers"]["Access-Control-Allow-Credentials"] is True
    
    body = json.loads(response["body"])
    assert body["message"] == "Success"
    
    # Test with custom status code
    response = build_response(201, data)
    assert response["statusCode"] == 201
    
    # Test with error status
    error_data = {"message": "Error occurred"}
    response = build_response(400, error_data)
    assert response["statusCode"] == 400
    
    body = json.loads(response["body"])
    assert body["message"] == "Error occurred"
    
    # Test with complex data containing Decimal
    complex_data = {
        "amount": decimal.Decimal("123.45"),
        "items": [
            {"price": decimal.Decimal("10.99"), "quantity": 2},
            {"price": decimal.Decimal("5.99"), "quantity": 1}
        ]
    }
    
    response = build_response(200, complex_data)
    body = json.loads(response["body"])
    
    assert body["amount"] == 123.45
    assert body["items"][0]["price"] == 10.99
    assert body["items"][1]["price"] == 5.99


@patch("functions.shared.utils.utils.tasks_table")
def test_get_task_by_id(mock_table):
    """Test retrieving a task by ID."""
    # Setup mock response
    mock_item = {
        "PK": "WORKSPACE#workspace-123",
        "SK": "TASK#task-123",
        "task_id": "task-123",
        "title": "Test Task",
        "workspace_id": "workspace-123",
        "status": "TODO"
    }
    mock_response = {"Item": mock_item}
    mock_table.get_item.return_value = mock_response
    
    # Call function
    task = get_task_by_id("workspace-123", "task-123")
    
    # Verify the result
    assert task is not None
    assert task == mock_item
    
    # Verify DynamoDB was called correctly
    mock_table.get_item.assert_called_once_with(
        Key={
            "PK": "WORKSPACE#workspace-123",
            "SK": "TASK#task-123"
        }
    )
    
    # Test task not found
    mock_table.get_item.return_value = {}
    task = get_task_by_id("workspace-123", "non-existent")
    assert task is None


@patch("functions.shared.utils.utils.accounts_table")
def test_validate_workspace_access(mock_table):
    """Test workspace access validation."""
    # Setup mock response for valid access
    mock_item = {
        "PK": "ACCOUNT#account-123",
        "SK": "WORKSPACE#workspace-123",
        "workspace_id": "workspace-123",
        "account_id": "account-123",
        "status": "ACTIVE"
    }
    mock_response = {"Item": mock_item}
    mock_table.get_item.return_value = mock_response
    
    # Test valid access
    has_access, error = validate_workspace_access("account-123", "workspace-123")
    assert has_access is True
    assert error is None
    
    # Verify DynamoDB was called correctly
    mock_table.get_item.assert_called_with(
        Key={
            "PK": "ACCOUNT#account-123",
            "SK": "WORKSPACE#workspace-123"
        }
    )
    
    # Test invalid access (workspace not found)
    mock_table.get_item.return_value = {}
    has_access, error = validate_workspace_access("account-123", "non-existent")
    assert has_access is False
    assert "not found" in error
    
    # Test inactive workspace
    mock_item["status"] = "INACTIVE"
    mock_table.get_item.return_value = {"Item": mock_item}
    has_access, error = validate_workspace_access("account-123", "workspace-123")
    assert has_access is False
    assert "inactive" in error.lower()
    
    # Test different account trying to access
    mock_item["status"] = "ACTIVE"
    mock_table.get_item.return_value = {"Item": mock_item}
    has_access, error = validate_workspace_access("different-account", "workspace-123")
    assert has_access is False
    assert "no access" in error.lower() 