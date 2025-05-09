"""Data models for Workspace Service."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

def generate_id(prefix="ws-"):
    """Generate a unique workspace ID with optional prefix."""
    return f"{prefix}{uuid.uuid4()}"

def get_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def create_workspace_item(account_id: str, workspace_name: str, owner_id: str, owner_email: str) -> Dict[str, Any]:
    """Create a DynamoDB item for a new workspace."""
    workspace_id = generate_id()
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
        "entity_type": "WORKSPACE",
        "GSI1PK": f"USER#{owner_id}",
        "GSI1SK": f"WORKSPACE#{workspace_id}"
    }

def create_workspace_user_role_item(
    account_id: str, 
    workspace_id: str, 
    user_id: str, 
    email: str, 
    role: str
) -> Dict[str, Any]:
    """Create a DynamoDB item for a user role in a workspace."""
    timestamp = get_timestamp()
    
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
        "entity_type": "USER_ROLE",
        "GSI1PK": f"USER#{user_id}",
        "GSI1SK": f"WORKSPACE#{workspace_id}"
    }

def validate_workspace_input(workspace_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate workspace creation input."""
    required_fields = ["workspace_name", "account_id"]
    
    for field in required_fields:
        if field not in workspace_data or not workspace_data[field]:
            return False, f"Missing required field: {field}"
    
    return True, None 