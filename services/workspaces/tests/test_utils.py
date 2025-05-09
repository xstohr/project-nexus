"""Tests for the utility functions module."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.workspaces.functions.shared.utils.utils import (
    get_user_from_event,
    build_response,
    get_workspace_by_id
)

def test_get_user_from_event_with_auth_header():
    """Test extracting user from event with auth header."""
    event = {
        "headers": {
            "Authorization": "Bearer test-token"
        }
    }
    
    user = get_user_from_event(event)
    assert user["user_id"] == "test-user-id"
    assert user["email"] == "test@example.com"
    assert user["tenant_id"] == "test-tenant-id"

def test_get_user_from_event_without_auth_header():
    """Test extracting user from event without auth header."""
    event = {"headers": {}}
    
    user = get_user_from_event(event)
    assert user["user_id"] == "test-user-id"
    assert user["email"] == "test@example.com"
    assert user["tenant_id"] == "test-tenant-id"

def test_get_user_from_event_no_headers():
    """Test extracting user from event with no headers."""
    event = {}
    
    user = get_user_from_event(event)
    assert user["user_id"] == "test-user-id"
    assert user["email"] == "test@example.com"
    assert user["tenant_id"] == "test-tenant-id"

def test_build_response():
    """Test building API responses."""
    # Test success response
    success_response = build_response(200, {"message": "Success"})
    assert success_response["statusCode"] == 200
    assert json.loads(success_response["body"]) == {"message": "Success"}
    assert success_response["headers"]["Content-Type"] == "application/json"
    assert success_response["headers"]["Access-Control-Allow-Origin"] == "*"
    
    # Test error response
    error_response = build_response(400, {"error": "Bad request"})
    assert error_response["statusCode"] == 400
    assert json.loads(error_response["body"]) == {"error": "Bad request"}

def test_get_workspace_by_id_found(mock_workspace_item):
    """Test retrieving workspace by ID when found."""
    with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
        # Configure mock to return a workspace
        mock_accounts_table.query.return_value = {"Items": [mock_workspace_item]}
        
        workspace = get_workspace_by_id("test-workspace-id")
        assert workspace is not None
        assert workspace["workspace_id"] == mock_workspace_item["workspace_id"]
        assert workspace["workspace_name"] == mock_workspace_item["workspace_name"]
        
        # Verify the query was called correctly
        mock_accounts_table.query.assert_called_once()
        call_args = mock_accounts_table.query.call_args[1]
        assert call_args["IndexName"] == "WorkspaceIdIndex"
        assert ":workspace_id" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":workspace_id"] == "test-workspace-id"

def test_get_workspace_by_id_not_found():
    """Test retrieving workspace by ID when not found."""
    with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
        # Configure mock to return no items
        mock_accounts_table.query.return_value = {"Items": []}
        
        workspace = get_workspace_by_id("nonexistent-workspace-id")
        assert workspace is None
        
        # Verify the query was called correctly
        mock_accounts_table.query.assert_called_once()

def test_get_workspace_by_id_exception():
    """Test error handling in get_workspace_by_id function."""
    with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
        # Configure mock to raise an exception
        mock_accounts_table.query.side_effect = Exception("Test exception")
        
        workspace = get_workspace_by_id("test-workspace-id")
        assert workspace is None
        
        # Verify the query was called
        mock_accounts_table.query.assert_called_once()


if __name__ == "__main__":
    pytest.main() 