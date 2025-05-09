"""Tests for the workspace models module."""

import pytest
from services.workspaces.functions.shared.models.workspace_models import (
    generate_id,
    get_timestamp,
    create_workspace_item,
    create_workspace_user_role_item,
    validate_workspace_input
)

def test_generate_id():
    """Test the ID generation function."""
    # Test with default prefix
    workspace_id = generate_id()
    assert workspace_id.startswith("ws-")
    assert len(workspace_id) > 3  # Should have uuid after prefix
    
    # Test with custom prefix
    custom_id = generate_id(prefix="custom-")
    assert custom_id.startswith("custom-")
    assert len(custom_id) > 7

def test_get_timestamp():
    """Test the timestamp generation function."""
    timestamp = get_timestamp()
    assert isinstance(timestamp, str)
    # Basic check for ISO format: contains T and has the right length
    assert "T" in timestamp
    assert len(timestamp) >= 19  # At least YYYY-MM-DDTHH:MM:SS

def test_create_workspace_item():
    """Test workspace item creation."""
    account_id = "test-account"
    workspace_name = "Test Workspace"
    owner_id = "test-user"
    owner_email = "test@example.com"
    
    workspace_item = create_workspace_item(account_id, workspace_name, owner_id, owner_email)
    
    # Check required fields
    assert "PK" in workspace_item
    assert workspace_item["PK"] == f"ACCOUNT#{account_id}"
    assert "SK" in workspace_item
    assert "workspace_id" in workspace_item
    assert workspace_item["workspace_name"] == workspace_name
    assert workspace_item["owner_id"] == owner_id
    assert workspace_item["account_id"] == account_id
    assert workspace_item["status"] == "ACTIVE"
    assert "created_at" in workspace_item
    assert "updated_at" in workspace_item
    assert workspace_item["entity_type"] == "WORKSPACE"
    assert workspace_item["GSI1PK"] == f"USER#{owner_id}"
    assert "GSI1SK" in workspace_item

def test_create_workspace_user_role_item():
    """Test user role item creation."""
    account_id = "test-account"
    workspace_id = "test-workspace"
    user_id = "test-user"
    email = "test@example.com"
    role = "ADMIN"
    
    user_role_item = create_workspace_user_role_item(account_id, workspace_id, user_id, email, role)
    
    # Check required fields
    assert "PK" in user_role_item
    assert user_role_item["PK"] == f"WORKSPACE#{workspace_id}"
    assert "SK" in user_role_item
    assert user_role_item["SK"] == f"USER#{user_id}"
    assert user_role_item["account_id"] == account_id
    assert user_role_item["workspace_id"] == workspace_id
    assert user_role_item["user_id"] == user_id
    assert user_role_item["email"] == email
    assert user_role_item["role"] == role
    assert "created_at" in user_role_item
    assert "updated_at" in user_role_item
    assert user_role_item["entity_type"] == "USER_ROLE"
    assert user_role_item["GSI1PK"] == f"USER#{user_id}"
    assert user_role_item["GSI1SK"] == f"WORKSPACE#{workspace_id}"

@pytest.mark.parametrize("test_case", [
    {"description": "Valid input", "input": {"workspace_name": "Test", "account_id": "acc123"}, "valid": True, "error": None},
    {"description": "Missing workspace_name", "input": {"account_id": "acc123"}, "valid": False, "error": "Missing required field: workspace_name"},
    {"description": "Missing account_id", "input": {"workspace_name": "Test"}, "valid": False, "error": "Missing required field: account_id"},
    {"description": "Empty workspace_name", "input": {"workspace_name": "", "account_id": "acc123"}, "valid": False, "error": "Missing required field: workspace_name"},
    {"description": "Empty account_id", "input": {"workspace_name": "Test", "account_id": ""}, "valid": False, "error": "Missing required field: account_id"},
])
def test_validate_workspace_input(test_case):
    """Test workspace input validation."""
    is_valid, error = validate_workspace_input(test_case["input"])
    assert is_valid == test_case["valid"]
    assert error == test_case["error"]


if __name__ == "__main__":
    pytest.main() 