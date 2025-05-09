"""Tests for the data models."""

import pytest
from datetime import datetime
from nexus.models import Resource, ResourceCollection


def test_resource_creation():
    """Test creating a Resource model."""
    resource = Resource(
        id="test-id",
        resource_type="test-resource",
        attributes={
            "name": "Test Resource",
            "value": 123
        }
    )
    
    assert resource.id == "test-id"
    assert resource.resource_type == "test-resource"
    assert resource.attributes["name"] == "Test Resource"
    assert resource.attributes["value"] == 123
    assert resource.created_at is not None
    assert isinstance(resource.created_at, datetime)
    assert resource.updated_at is None


def test_resource_to_dict():
    """Test converting a Resource to a dictionary."""
    # Create a resource with a known timestamp for deterministic testing
    created_at = datetime(2023, 1, 1, 12, 0, 0)
    resource = Resource(
        id="test-id",
        resource_type="test-resource",
        created_at=created_at,
        attributes={"name": "Test Resource"}
    )
    
    # Convert to dictionary
    data = resource.to_dict()
    
    # Verify the dictionary
    assert data["id"] == "test-id"
    assert data["resource_type"] == "test-resource"
    assert "created_at" in data
    assert "attributes" in data
    assert data["attributes"]["name"] == "Test Resource"
    assert "updated_at" not in data  # Should be excluded as it's None


def test_resource_from_dict():
    """Test creating a Resource from a dictionary."""
    # Create a dictionary
    data = {
        "id": "test-id",
        "resource_type": "test-resource",
        "created_at": "2023-01-01T12:00:00",
        "updated_at": "2023-01-02T12:00:00",
        "attributes": {"name": "Test Resource"}
    }
    
    # Create a Resource from the dictionary
    resource = Resource.from_dict(data)
    
    # Verify the resource
    assert resource.id == "test-id"
    assert resource.resource_type == "test-resource"
    assert resource.attributes["name"] == "Test Resource"
    assert isinstance(resource.created_at, datetime)
    assert isinstance(resource.updated_at, datetime)


def test_resource_collection():
    """Test creating a ResourceCollection."""
    # Create resources
    resources = [
        Resource(
            id=f"test-id-{i}",
            resource_type="test-resource",
            attributes={"name": f"Test Resource {i}"}
        )
        for i in range(3)
    ]
    
    # Create a collection
    collection = ResourceCollection(
        items=resources,
        count=3
    )
    
    # Verify the collection
    assert collection.count == 3
    assert len(collection.items) == 3
    assert collection.next_token is None
    
    # Add a next token
    collection.next_token = "next-page-token"
    assert collection.next_token == "next-page-token" 