"""Pytest configuration for workspace service tests."""

import os
import pytest
from unittest.mock import MagicMock

# Mock responses for DynamoDB operations
@pytest.fixture
def mock_workspace_item():
    """Mock workspace item from DynamoDB."""
    return {
        "PK": "ACCOUNT#test-account-id",
        "SK": "WORKSPACE#test-workspace-id",
        "workspace_id": "test-workspace-id",
        "workspace_name": "Test Workspace",
        "owner_id": "test-user-id",
        "account_id": "test-account-id",
        "status": "ACTIVE",
        "created_at": "2023-01-01T00:00:00.000Z",
        "updated_at": "2023-01-01T00:00:00.000Z",
        "entity_type": "WORKSPACE",
        "GSI1PK": "USER#test-user-id",
        "GSI1SK": "WORKSPACE#test-workspace-id"
    }

@pytest.fixture
def mock_account_item():
    """Mock account item from DynamoDB."""
    return {
        "PK": "ACCOUNT#test-account-id",
        "SK": "METADATA",
        "account_id": "test-account-id",
        "account_name": "Test Account",
        "owner_id": "test-user-id",
        "owner_email": "test@example.com",
        "status": "ACTIVE",
        "created_at": "2023-01-01T00:00:00.000Z",
        "updated_at": "2023-01-01T00:00:00.000Z",
        "entity_type": "ACCOUNT"
    }

@pytest.fixture
def mock_user_role_item():
    """Mock user role item from DynamoDB."""
    return {
        "PK": "WORKSPACE#test-workspace-id",
        "SK": "USER#test-user-id",
        "account_id": "test-account-id",
        "workspace_id": "test-workspace-id",
        "user_id": "test-user-id",
        "email": "test@example.com",
        "role": "ADMIN",
        "created_at": "2023-01-01T00:00:00.000Z",
        "updated_at": "2023-01-01T00:00:00.000Z",
        "entity_type": "USER_ROLE",
        "GSI1PK": "USER#test-user-id",
        "GSI1SK": "WORKSPACE#test-workspace-id"
    }

@pytest.fixture
def mock_user():
    """Mock user from auth token."""
    return {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "tenant_id": "test-tenant-id"
    }

@pytest.fixture
def mock_accounts_table():
    """Mock DynamoDB accounts table."""
    mock_table = MagicMock()
    return mock_table

@pytest.fixture
def mock_create_event():
    """Mock event for create workspace function."""
    return {
        "pathParameters": {"accountId": "test-account-id"},
        "body": '{"workspace_name": "Test Workspace"}'
    }

@pytest.fixture
def mock_get_event():
    """Mock event for get workspace function."""
    return {
        "pathParameters": {"workspaceId": "test-workspace-id"}
    }

@pytest.fixture
def mock_update_event():
    """Mock event for update workspace function."""
    return {
        "pathParameters": {"workspaceId": "test-workspace-id"},
        "body": '{"workspace_name": "Updated Workspace Name"}'
    }

@pytest.fixture
def mock_delete_event():
    """Mock event for delete workspace function."""
    return {
        "pathParameters": {"workspaceId": "test-workspace-id"}
    }

@pytest.fixture
def mock_list_event():
    """Mock event for list workspaces function."""
    return {
        "pathParameters": {"accountId": "test-account-id"}
    } 