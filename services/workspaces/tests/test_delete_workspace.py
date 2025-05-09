"""Tests for the delete_workspace Lambda function."""

import json
import pytest
from unittest.mock import patch

from services.workspaces.functions.workspace_operations.delete_workspace.delete_workspace import handler

@pytest.mark.parametrize("test_case", [
    {"description": "Successful workspace deletion", "status_code": 200},
])
def test_delete_workspace_success(test_case, mock_user, mock_workspace_item, mock_delete_event):
    """Test successful workspace deactivation."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
                # Configure mocks
                mock_get_user.return_value = mock_user
                mock_get_workspace.return_value = mock_workspace_item
                
                # Call the handler
                response = handler(mock_delete_event, {})
                
                # Assert response
                assert response["statusCode"] == test_case["status_code"]
                
                # Verify DynamoDB update was called
                mock_accounts_table.update_item.assert_called_once()
                
                # Parse response body
                body = json.loads(response["body"])
                assert body["message"] == "Workspace marked as inactive"
                assert body["workspace_id"] == mock_workspace_item["workspace_id"]
                assert body["account_id"] == mock_workspace_item["account_id"]

def test_delete_workspace_missing_id():
    """Test deletion with missing workspace ID."""
    # Create test event with missing workspace ID
    event = {"pathParameters": {}}
    
    # Call the handler
    response = handler(event, {})
    
    # Assert response
    assert response["statusCode"] == 400
    
    # Parse response body
    body = json.loads(response["body"])
    assert body["error"] == "Missing workspaceId parameter"

def test_delete_workspace_not_found(mock_user, mock_delete_event):
    """Test deletion with non-existent workspace."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.return_value = None
            
            # Call the handler
            response = handler(mock_delete_event, {})
            
            # Assert response
            assert response["statusCode"] == 404
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Workspace not found"

def test_delete_workspace_exception(mock_user, mock_workspace_item, mock_delete_event):
    """Test error handling in delete function."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
                # Configure mocks
                mock_get_user.return_value = mock_user
                mock_get_workspace.return_value = mock_workspace_item
                mock_accounts_table.update_item.side_effect = Exception("Test exception")
                
                # Call the handler
                response = handler(mock_delete_event, {})
                
                # Assert response
                assert response["statusCode"] == 500
                
                # Parse response body
                body = json.loads(response["body"])
                assert body["error"] == "Failed to deactivate workspace"


if __name__ == "__main__":
    pytest.main() 