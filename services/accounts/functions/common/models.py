"""Data models for Account Service."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

def generate_id(prefix=""):
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{uuid.uuid4()}"

def get_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def create_account_item(account_name: str, owner_id: str, owner_email: str) -> Dict[str, Any]:
    """Create a DynamoDB item for a new account."""
    account_id = generate_id("acc-")
    timestamp = get_timestamp()
    
    return {
        "PK": f"ACCOUNT#{account_id}",
        "SK": "METADATA",
        "account_id": account_id,
        "account_name": account_name,
        "owner_id": owner_id,
        "owner_email": owner_email,
        "status": "ACTIVE",
        "tier": "FREE",
        "created_at": timestamp,
        "updated_at": timestamp,
        "entity_type": "ACCOUNT"
    }

def create_workspace_item(account_id: str, workspace_name: str, owner_id: str) -> Dict[str, Any]:
    """Create a DynamoDB item for a new workspace."""
    workspace_id = generate_id("ws-")
    timestamp = get_timestamp()
    
    return {
        "PK": f"ACCOUNT#{account_id}",
        "SK": f"WORKSPACE#{workspace_id}",
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "owner_id": owner_id,
        "account_id": account_id,
        "status": "ACTIVE",
        "created_at": timestamp,
        "updated_at": timestamp,
        "entity_type": "WORKSPACE"
    }

def create_user_role_item(account_id: str, workspace_id: Optional[str], user_id: str, 
                         email: str, role: str) -> Dict[str, Any]:
    """Create a DynamoDB item for a user role assignment.
    
    If workspace_id is None, this is an account-level role.
    If workspace_id is provided, this is a workspace-level role.
    """
    timestamp = get_timestamp()
    
    if workspace_id:
        # Workspace-level role
        return {
            "PK": f"WORKSPACE#{workspace_id}",
            "SK": f"USER#{user_id}",
            "account_id": account_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "email": email,
            "role": role,
            "created_at": timestamp,
            "updated_at": timestamp,
            "entity_type": "USER_ROLE"
        }
    else:
        # Account-level role
        return {
            "PK": f"ACCOUNT#{account_id}",
            "SK": f"USER#{user_id}",
            "account_id": account_id,
            "user_id": user_id,
            "email": email,
            "role": role,
            "created_at": timestamp,
            "updated_at": timestamp,
            "entity_type": "USER_ROLE"
        }

def validate_account_input(account_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate account creation input."""
    required_fields = ["account_name", "owner_email"]
    
    for field in required_fields:
        if field not in account_data or not account_data[field]:
            return False, f"Missing required field: {field}"
    
    # Additional validation logic could be added here
    return True, None

def validate_workspace_input(workspace_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate workspace creation input."""
    required_fields = ["workspace_name", "account_id"]
    
    for field in required_fields:
        if field not in workspace_data or not workspace_data[field]:
            return False, f"Missing required field: {field}"
    
    # Additional validation logic could be added here
    return True, None 