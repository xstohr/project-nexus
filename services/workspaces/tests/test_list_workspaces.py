"""Tests for the list_workspaces Lambda function."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.workspaces.functions.workspace_operations.list_workspaces.list_workspaces import handler

@pytest.mark.parametrize("test_case", [
    {"description": "List workspaces with results", "status_code": 200, "item_count": 2},
    {"description": "List workspaces with no results", "status_code": 200, "item_count": 0},
])
def test_list_workspaces_success(test_case, mock_user, mock_workspace_item, mock_list_event):
    """Test successful workspace listing."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
            # Configure mocks
            mock_get_user.return_value = mock_user
            
            # Create mock items for the query response
            items = []
            for i in range(test_case["item_count"]):
                workspace = mock_workspace_item.copy()
                workspace["workspace_id"] = f"test-workspace-{i}"
                workspace["workspace_name"] = f"Test Workspace {i}"
                items.append(workspace)
            
            mock_accounts_table.query.return_value = {"Items": items}
            
            # Call the handler
            response = handler(mock_list_event, {})
            
            # Assert response
            assert response["statusCode"] == test_case["status_code"]
            
            # Parse response body
            body = json.loads(response["body"])
            assert "workspaces" in body
            assert len(body["workspaces"]) == test_case["item_count"]
            
            # Verify each workspace has the expected fields
            for i, workspace in enumerate(body["workspaces"]):
                if test_case["item_count"] > 0:
                    assert workspace["workspace_id"] == f"test-workspace-{i}"
                    assert workspace["workspace_name"] == f"Test Workspace {i}"
                    assert "account_id" in workspace
                    assert "owner_id" in workspace
                    assert "status" in workspace
                    assert "created_at" in workspace

def test_list_workspaces_missing_account_id():
    """Test listing with missing account ID."""
    # Create test event with missing account ID
    event = {"pathParameters": {}}
    
    # Call the handler
    response = handler(event, {})
    
    # Assert response
    assert response["statusCode"] == 400
    
    # Parse response body
    body = json.loads(response["body"])
    assert body["error"] == "Missing accountId parameter"

def test_list_workspaces_exception(mock_user, mock_list_event):
    """Test error handling in list function."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
            # Configure mocks
            mock_get_user.return_value = mock_user
            mock_accounts_table.query.side_effect = Exception("Test exception")
            
            # Call the handler
            response = handler(mock_list_event, {})
            
            # Assert response
            assert response["statusCode"] == 500
            
            # Parse response body
            body = json.loads(response["body"])
            assert body["error"] == "Failed to list workspaces"

def test_list_workspaces_inactive_filtered(mock_user, mock_list_event):
    """Test that inactive workspaces are filtered out."""
    # Setup
    with patch('services.workspaces.functions.shared.utils.utils.get_user_from_event') as mock_get_user:
        with patch('services.workspaces.functions.shared.utils.utils.accounts_table') as mock_accounts_table:
            # Configure mocks
            mock_get_user.return_value = mock_user
            
            # Create mock items with both active and inactive workspaces
            items = [
                {
                    "PK": "ACCOUNT#test-account-id",
                    "SK": "WORKSPACE#test-workspace-1",
                    "workspace_id": "test-workspace-1",
                    "workspace_name": "Active Workspace",
                    "owner_id": "test-user-id",
                    "account_id": "test-account-id",
                    "status": "ACTIVE",
                    "created_at": "2023-01-01T00:00:00.000Z",
                    "entity_type": "WORKSPACE"
                },
                {
                    "PK": "ACCOUNT#test-account-id",
                    "SK": "WORKSPACE#test-workspace-2",
                    "workspace_id": "test-workspace-2",
                    "workspace_name": "Inactive Workspace",
                    "owner_id": "test-user-id",
                    "account_id": "test-account-id",
                    "status": "INACTIVE",
                    "created_at": "2023-01-01T00:00:00.000Z",
                    "entity_type": "WORKSPACE"
                },
                {
                    "PK": "ACCOUNT#test-account-id",
                    "SK": "USER#test-user-id",
                    "entity_type": "USER_ROLE"  # This should be filtered out too
                }
            ]
            
            mock_accounts_table.query.return_value = {"Items": items}
            
            # Call the handler
            response = handler(mock_list_event, {})
            
            # Assert response
            assert response["statusCode"] == 200
            
            # Parse response body
            body = json.loads(response["body"])
            assert len(body["workspaces"]) == 1
            assert body["workspaces"][0]["workspace_id"] == "test-workspace-1"
            assert body["workspaces"][0]["status"] == "ACTIVE"


if __name__ == "__main__":
    pytest.main() 