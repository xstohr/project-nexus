"""Tests for the get_workspace Lambda function."""

import json
import pytest
from unittest.mock import patch

from services.workspaces.functions.workspace_operations.get_workspace.get_workspace import handler

@pytest.mark.parametrize("test_case", [
    {"description": "Successful workspace retrieval", "status_code": 200},
])
def test_get_workspace_success(test_case, mock_user, mock_workspace_item, mock_get_event):
    """Test successful workspace retrieval."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.return_value = mock_workspace_item
            
            # Call the handler
            response = handler(mock_get_event, {})
            
            # Assert response
            assert response["statusCode"] == test_case["status_code"]
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["workspace_id"] == mock_workspace_item["workspace_id"]
            assert body["workspace_name"] == mock_workspace_item["workspace_name"]
            assert body["account_id"] == mock_workspace_item["account_id"]

def test_get_workspace_missing_id(mock_user):
    """Test workspace retrieval with missing workspace ID."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        # Configure mocks
        mock_get_user.return_value = mock_user
        
        # Create test event with missing workspace ID
        event = {"pathParameters": {}}
        
        # Call the handler
        response = handler(event, {})
        
        # Assert response
        assert response["statusCode"] == 400
        
        # Parse response body
        body = json.loads(response["body"])
        assert body["error"] == "Missing workspaceId parameter"

def test_get_workspace_not_found(mock_user, mock_get_event):
    """Test workspace retrieval with non-existent workspace."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.return_value = None
            
            # Call the handler
            response = handler(mock_get_event, {})
            
            # Assert response
            assert response["statusCode"] == 404
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Workspace not found"

def test_get_workspace_exception(mock_user, mock_get_event):
    """Test error handling in get workspace function."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.get_workspace_by_id') as mock_get_workspace:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_get_workspace.side_effect = Exception("Test exception")
            
            # Call the handler
            response = handler(mock_get_event, {})
            
            # Assert response
            assert response["statusCode"] == 500
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Failed to retrieve workspace"


if __name__ == "__main__":
    pytest.main() 