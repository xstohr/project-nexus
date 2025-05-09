"""Services for interacting with AWS resources."""

import os
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Type

from nexus.models import Resource, ResourceCollection


class DynamoDBService:
    """Service for interacting with DynamoDB."""
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize the DynamoDB service.
        
        Args:
            table_name: The name of the DynamoDB table to use.
                        If not provided, uses the DYNAMODB_TABLE environment variable.
        """
        self.table_name = table_name or os.environ.get("DYNAMODB_TABLE", "nexus-dev")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_resource(self, resource: Resource) -> Resource:
        """Create a new resource in DynamoDB.
        
        Args:
            resource: The resource to create.
            
        Returns:
            The created resource with updated metadata.
        """
        # Set creation timestamp
        now = datetime.utcnow()
        resource.created_at = now
        resource.updated_at = now
        
        # Generate an ID if not provided
        if not resource.id:
            resource.id = str(uuid.uuid4())
        
        # Save to DynamoDB
        self.table.put_item(Item=resource.to_dict())
        
        return resource
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID.
        
        Args:
            resource_id: The ID of the resource to get.
            
        Returns:
            The resource if found, None otherwise.
        """
        response = self.table.get_item(Key={"id": resource_id})
        item = response.get("Item")
        
        if not item:
            return None
        
        return Resource.from_dict(item)
    
    def update_resource(self, resource_id: str, updates: Dict[str, Any]) -> Optional[Resource]:
        """Update a resource.
        
        Args:
            resource_id: The ID of the resource to update.
            updates: The fields to update.
            
        Returns:
            The updated resource if found, None otherwise.
        """
        # Get the existing resource
        existing = self.get_resource(resource_id)
        if not existing:
            return None
        
        # Update fields
        for key, value in updates.items():
            setattr(existing, key, value)
        
        # Set update timestamp
        existing.updated_at = datetime.utcnow()
        
        # Save to DynamoDB
        self.table.put_item(Item=existing.to_dict())
        
        return existing
    
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource.
        
        Args:
            resource_id: The ID of the resource to delete.
            
        Returns:
            True if the resource was deleted, False otherwise.
        """
        response = self.table.delete_item(
            Key={"id": resource_id},
            ReturnValues="ALL_OLD"
        )
        
        return "Attributes" in response
    
    def list_resources(
        self, 
        limit: int = 50, 
        next_token: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> ResourceCollection:
        """List resources with pagination.
        
        Args:
            limit: Maximum number of items to return.
            next_token: Token for pagination.
            filter_expr: Filter expression for results.
            
        Returns:
            A collection of resources.
        """
        scan_kwargs = {
            "Limit": limit,
        }
        
        if next_token:
            scan_kwargs["ExclusiveStartKey"] = {"id": next_token}
        
        if filter_expr:
            scan_kwargs["FilterExpression"] = filter_expr
        
        response = self.table.scan(**scan_kwargs)
        
        # Create resources from items
        resources = [Resource.from_dict(item) for item in response.get("Items", [])]
        
        # Create the collection
        collection = ResourceCollection(
            items=resources,
            count=response.get("Count", 0),
        )
        
        # Set next token if available
        if "LastEvaluatedKey" in response:
            collection.next_token = response["LastEvaluatedKey"]["id"]
        
        return collection 