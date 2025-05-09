"""Data models for the Nexus application."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class Resource(BaseModel):
    """Base resource model for Nexus entities."""
    
    id: str = Field(..., description="Unique identifier for the resource")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    resource_type: str = Field(..., description="Type of resource")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to a dictionary for storage."""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resource":
        """Create a model instance from a dictionary."""
        return cls(**data)


class ResourceCollection(BaseModel):
    """Collection of resources with pagination."""
    
    items: List[Resource] = Field(default_factory=list, description="List of resources")
    count: int = Field(..., description="Total number of items in the collection")
    next_token: Optional[str] = Field(None, description="Token for retrieving the next page") 