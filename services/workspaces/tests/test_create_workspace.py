"""Tests for the create_workspace Lambda function."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.workspaces.functions.workspace_operations.create_workspace.create_workspace import handler

@pytest.mark.parametrize("test_case", [
    {"description": "Successful workspace creation", "status_code": 201},
])
def test_create_workspace_success(test_case, mock_user, mock_account_item, mock_create_event):
    """Test successful workspace creation."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_accounts_table.get_item.return_value = {"Item": mock_account_item}
            
            # Call the handler
            response = handler(mock_create_event, {})
            
            # Assert response
            assert response["statusCode"] == test_case["status_code"]
            
            # Verify DynamoDB interactions
            assert mock_accounts_table.put_item.call_count == 2
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["message"] == "Workspace created successfully"
            assert "workspace_id" in body
            assert body["workspace_name"] == "Test Workspace"
            assert body["account_id"] == "test-account-id"

@pytest.mark.parametrize("test_case", [
    {"description": "Missing accountId", "event_key": "pathParameters", "event_value": {}, "status_code": 400},
    {"description": "Missing workspace_name", "event_key": "body", "event_value": '{}', "status_code": 400},
])
def test_create_workspace_missing_params(test_case, mock_user, mock_create_event):
    """Test workspace creation with missing parameters."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        # Configure mocks
        mock_get_user.return_value = mock_user
        
        # Modify the event based on the test case
        modified_event = mock_create_event.copy()
        modified_event[test_case["event_key"]] = test_case["event_value"]
        
        # Call the handler
        response = handler(modified_event, {})
        
        # Assert response
        assert response["statusCode"] == test_case["status_code"]

def test_create_workspace_account_not_found(mock_user, mock_create_event):
    """Test workspace creation with non-existent account."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_accounts_table.get_item.return_value = {}
            
            # Call the handler
            response = handler(mock_create_event, {})
            
            # Assert response
            assert response["statusCode"] == 404
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Account not found"


if __name__ == "__main__":
    pytest.main() 