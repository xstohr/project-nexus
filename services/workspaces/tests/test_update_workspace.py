"""Tests for the update_workspace Lambda function."""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.workspaces.functions.workspace_operations.update_workspace.update_workspace import handler

@pytest.mark.parametrize("test_case", [
    {"description": "Update workspace name", "status_code": 200, "update_body": '{"workspace_name": "Updated Workspace"}'},
    {"description": "Update workspace status", "status_code": 200, "update_body": '{"status": "INACTIVE"}'},
    {"description": "Update both name and status", "status_code": 200, "update_body": '{"workspace_name": "Updated Workspace", "status": "INACTIVE"}'},
])
def test_update_workspace_success(test_case, mock_user, mock_workspace_item, mock_update_event):
    """Test successful workspace updates."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
                # Configure mocks
                mock_get_user.return_value = mock_user
                mock_get_workspace.return_value = mock_workspace_item
                
                # Modify event with test case body
                event = mock_update_event.copy()
                event["body"] = test_case["update_body"]
                
                # Call the handler
                response = handler(event, {})
                
                # Assert response
                assert response["statusCode"] == test_case["status_code"]
                
                # Verify DynamoDB update was called
                mock_accounts_table.update_item.assert_called_once()
                
                # Parse response body
                body = json.loads(response["body"])
                assert body["message"] == "Workspace updated successfully"
                assert body["workspace_id"] == mock_workspace_item["workspace_id"]
                assert body["account_id"] == mock_workspace_item["account_id"]

def test_update_workspace_missing_id():
    """Test update with missing workspace ID."""
    # Create test event with missing workspace ID
    event = {"pathParameters": {}, "body": '{"workspace_name": "Updated Workspace"}'}
    
    # Call the handler
    response = handler(event, {})
    
    # Assert response
    assert response["statusCode"] == 400
    
    # Parse response body
    body = json.loads(response["body"])
    assert body["error"] == "Missing workspaceId parameter"

def test_update_workspace_empty_body(mock_user, mock_workspace_item):
    """Test update with empty request body."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.return_value = mock_workspace_item
            
            # Create event with empty body
            event = {"pathParameters": {"workspaceId": "test-workspace-id"}, "body": "{}"}
            
            # Call the handler
            response = handler(event, {})
            
            # Assert response
            assert response["statusCode"] == 400
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Request body is required"

def test_update_workspace_not_found(mock_user, mock_update_event):
    """Test update with non-existent workspace."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.return_value = None
            
            # Call the handler
            response = handler(mock_update_event, {})
            
            # Assert response
            assert response["statusCode"] == 404
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Workspace not found"

def test_update_workspace_exception(mock_user, mock_workspace_item, mock_update_event):
    """Test error handling in update function."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
                # Configure mocks
                mock_get_user.return_value = mock_user
                mock_get_workspace.return_value = mock_workspace_item
                mock_accounts_table.update_item.side_effect = Exception("Test exception")
                
                # Call the handler
                response = handler(mock_update_event, {})
                
                # Assert response
                assert response["statusCode"] == 500
                
                # Parse response body
                body = json.loads(response["body"])
                assert body["error"] == "Failed to update workspace"


if __name__ == "__main__":
    pytest.main() 