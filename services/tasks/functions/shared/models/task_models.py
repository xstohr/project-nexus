"""Data models for Tasks Service."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

def generate_id(prefix="task-"):
    """Generate a unique task ID with optional prefix."""
    return f"{prefix}{uuid.uuid4()}"

def get_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def create_task_item(
    workspace_id: str, 
    account_id: str,
    title: str, 
    description: Optional[str] = None, 
    status: str = "BACKLOG",
    priority: str = "MEDIUM",
    assignee_id: Optional[str] = None,
    creator_id: str = "",
    creator_email: str = "",
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a DynamoDB item for a new task."""
    task_id = generate_id()
    timestamp = get_timestamp()
    
    item = {
        "PK": f"WORKSPACE#{workspace_id}",
        "SK": f"TASK#{task_id}",
        "task_id": task_id,
        "title": title,
        "workspace_id": workspace_id,
        "account_id": account_id,
        "status": status,
        "priority": priority,
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_by": {
            "user_id": creator_id,
            "email": creator_email
        },
        "entity_type": "TASK",
        "GSI1PK": f"WORKSPACE#{workspace_id}",  # For querying tasks by workspace
        "GSI1SK": f"STATUS#{status}#PRIORITY#{priority}#TASK#{task_id}"  # For sorting
    }
    
    # Add optional fields
    if description:
        item["description"] = description
    
    if assignee_id:
        item["assignee_id"] = assignee_id
        item["GSI2PK"] = f"WORKSPACE#{workspace_id}"  # For querying tasks by assignee
        item["GSI2SK"] = f"ASSIGNEE#{assignee_id}#TASK#{task_id}"
    
    if due_date:
        item["due_date"] = due_date
    
    if tags and len(tags) > 0:
        item["tags"] = tags
    
    return item

def validate_task_input(task_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate task creation/update input."""
    # Required fields for creation
    if "title" not in task_data or not task_data["title"]:
        return False, "Missing required field: title"
    
    # Validate status if provided
    if "status" in task_data:
        valid_statuses = ["BACKLOG", "TODO", "IN_PROGRESS", "DONE"]
        if task_data["status"] not in valid_statuses:
            return False, f"Invalid status value. Must be one of: {', '.join(valid_statuses)}"
    
    # Validate priority if provided
    if "priority" in task_data:
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
        if task_data["priority"] not in valid_priorities:
            return False, f"Invalid priority value. Must be one of: {', '.join(valid_priorities)}"
    
    # Validate tags if provided
    if "tags" in task_data:
        if not isinstance(task_data["tags"], list):
            return False, "Tags must be an array of strings"
        
        for tag in task_data["tags"]:
            if not isinstance(tag, str):
                return False, "All tags must be strings"
    
    return True, None

def prepare_update_expression(task_data: Dict[str, Any]) -> tuple[str, Dict[str, Any], Dict[str, str]]:
    """Prepare DynamoDB update expression for task updates."""
    update_expression = "SET updated_at = :updated_at"
    expression_attr_values = {":updated_at": get_timestamp()}
    expression_attr_names = {}
    
    # Map of field names to their DynamoDB attribute names
    field_mappings = {
        "title": "title",
        "description": "description",
        "status": "status",
        "priority": "priority",
        "assignee_id": "assignee_id",
        "due_date": "due_date",
        "tags": "tags"
    }
    
    # Add each field to the update expression
    for field, attr_name in field_mappings.items():
        if field in task_data:
            # If using an expression attribute name
            expression_attr_names[f"#{attr_name}"] = attr_name
            expression_attr_values[f":{field}"] = task_data[field]
            update_expression += f", #{attr_name} = :{field}"
    
    # Special handling for GSI sort keys if status or priority changes
    if "status" in task_data or "priority" in task_data:
        task = task_data.get("_existing_task", {})
        
        # Get current or new values
        status = task_data.get("status", task.get("status", "BACKLOG"))
        priority = task_data.get("priority", task.get("priority", "MEDIUM"))
        
        # Update GSI1SK
        expression_attr_values[":gsi1sk"] = f"STATUS#{status}#PRIORITY#{priority}#TASK#{task.get('task_id', '')}"
        expression_attr_names["#GSI1SK"] = "GSI1SK"
        update_expression += ", #GSI1SK = :gsi1sk"
    
    # Special handling for assignee changes
    if "assignee_id" in task_data:
        task = task_data.get("_existing_task", {})
        workspace_id = task.get("workspace_id", "")
        task_id = task.get("task_id", "")
        
        if task_data["assignee_id"]:
            # Add or update GSI2 keys for assignee lookup
            expression_attr_values[":gsi2pk"] = f"WORKSPACE#{workspace_id}"
            expression_attr_values[":gsi2sk"] = f"ASSIGNEE#{task_data['assignee_id']}#TASK#{task_id}"
            expression_attr_names["#GSI2PK"] = "GSI2PK"
            expression_attr_names["#GSI2SK"] = "GSI2SK"
            update_expression += ", #GSI2PK = :gsi2pk, #GSI2SK = :gsi2sk"
        elif "GSI2PK" in task and "GSI2SK" in task:
            # Remove GSI2 keys if assignee is being removed
            update_expression += " REMOVE GSI2PK, GSI2SK"
    
    return update_expression, expression_attr_values, expression_attr_names 