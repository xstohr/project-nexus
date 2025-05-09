"""Pytest fixtures for the Nexus application."""

import os
import pytest
import boto3
import json
from moto import mock_dynamodb
from typing import Dict, Any, Generator

from nexus.models import Resource
from nexus.services import DynamoDBService


@pytest.fixture
def event_data() -> Dict[str, Any]:
    """Load the sample API Gateway event data."""
    event_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "events", "event.json")
    with open(event_path, "r") as f:
        return json.load(f)


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context object."""
    class LambdaContext:
        def __init__(self):
            self.function_name = "test-function"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:eu-west-1:123456789012:function:test-function"
            self.aws_request_id = "request-id"

    return LambdaContext()


@pytest.fixture
def dynamodb_table() -> Generator:
    """Create a mock DynamoDB table."""
    with mock_dynamodb():
        # Set environment variables for testing
        os.environ["DYNAMODB_TABLE"] = "nexus-test"
        
        # Create mock DynamoDB resources
        dynamodb = boto3.resource("dynamodb")
        
        # Create mock table
        table = dynamodb.create_table(
            TableName="nexus-test",
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        yield table
        
        # Clean up
        table.delete()


@pytest.fixture
def dynamodb_service(dynamodb_table) -> DynamoDBService:
    """Create a DynamoDBService instance with the mock table."""
    return DynamoDBService(table_name="nexus-test")


@pytest.fixture
def sample_resource() -> Resource:
    """Create a sample resource for testing."""
    return Resource(
        id="test-id",
        resource_type="test-resource",
        attributes={
            "name": "Test Resource",
            "description": "A test resource for unit testing"
        }
    ) 