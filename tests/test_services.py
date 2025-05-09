"""Tests for the DynamoDB service."""

import pytest
from nexus.services import DynamoDBService
from nexus.models import Resource


def test_create_resource(dynamodb_service, sample_resource):
    """Test creating a resource in DynamoDB."""
    # Create the resource
    created = dynamodb_service.create_resource(sample_resource)
    
    # Verify the resource was created with the expected values
    assert created.id == sample_resource.id
    assert created.resource_type == sample_resource.resource_type
    assert created.attributes == sample_resource.attributes
    assert created.created_at is not None
    assert created.updated_at is not None


def test_get_resource(dynamodb_service, sample_resource):
    """Test getting a resource from DynamoDB."""
    # Create a resource first
    dynamodb_service.create_resource(sample_resource)
    
    # Get the resource
    retrieved = dynamodb_service.get_resource(sample_resource.id)
    
    # Verify the retrieved resource
    assert retrieved is not None
    assert retrieved.id == sample_resource.id
    assert retrieved.resource_type == sample_resource.resource_type
    assert retrieved.attributes == sample_resource.attributes


def test_get_nonexistent_resource(dynamodb_service):
    """Test getting a nonexistent resource from DynamoDB."""
    # Try to get a nonexistent resource
    retrieved = dynamodb_service.get_resource("nonexistent-id")
    
    # Verify the result is None
    assert retrieved is None


def test_update_resource(dynamodb_service, sample_resource):
    """Test updating a resource in DynamoDB."""
    # Create a resource first
    dynamodb_service.create_resource(sample_resource)
    
    # Define updates
    updates = {
        "resource_type": "updated-type",
        "attributes": {
            "name": "Updated Resource",
            "description": "An updated test resource"
        }
    }
    
    # Update the resource
    updated = dynamodb_service.update_resource(sample_resource.id, updates)
    
    # Verify the updates
    assert updated is not None
    assert updated.id == sample_resource.id
    assert updated.resource_type == "updated-type"
    assert updated.attributes["name"] == "Updated Resource"
    assert updated.attributes["description"] == "An updated test resource"
    assert updated.updated_at is not None
    
    # Retrieve the resource to verify persistence
    retrieved = dynamodb_service.get_resource(sample_resource.id)
    assert retrieved.resource_type == "updated-type"


def test_update_nonexistent_resource(dynamodb_service):
    """Test updating a nonexistent resource in DynamoDB."""
    # Try to update a nonexistent resource
    updated = dynamodb_service.update_resource("nonexistent-id", {"resource_type": "new-type"})
    
    # Verify the result is None
    assert updated is None


def test_delete_resource(dynamodb_service, sample_resource):
    """Test deleting a resource from DynamoDB."""
    # Create a resource first
    dynamodb_service.create_resource(sample_resource)
    
    # Delete the resource
    result = dynamodb_service.delete_resource(sample_resource.id)
    
    # Verify the deletion was successful
    assert result is True
    
    # Try to get the deleted resource
    retrieved = dynamodb_service.get_resource(sample_resource.id)
    assert retrieved is None


def test_delete_nonexistent_resource(dynamodb_service):
    """Test deleting a nonexistent resource from DynamoDB."""
    # Try to delete a nonexistent resource
    result = dynamodb_service.delete_resource("nonexistent-id")
    
    # Verify the result indicates no deletion occurred
    assert result is False


def test_list_resources(dynamodb_service):
    """Test listing resources from DynamoDB."""
    # Create multiple resources
    resources = []
    for i in range(5):
        resource = Resource(
            id=f"test-id-{i}",
            resource_type="test-resource",
            attributes={"name": f"Test Resource {i}"}
        )
        dynamodb_service.create_resource(resource)
        resources.append(resource)
    
    # List resources
    collection = dynamodb_service.list_resources()
    
    # Verify the collection
    assert collection.count == 5
    assert len(collection.items) == 5
    
    # Verify pagination
    collection = dynamodb_service.list_resources(limit=2)
    assert len(collection.items) == 2
    assert collection.next_token is not None 