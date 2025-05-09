"""Tests for the hello world Lambda function."""

import json
from nexus.functions.hello_world.app import lambda_handler


def test_lambda_handler(event_data, lambda_context):
    """Test that the lambda_handler returns the expected response."""
    # Call the lambda function
    response = lambda_handler(event_data, lambda_context)
    
    # Verify the response structure
    assert isinstance(response, dict)
    assert "statusCode" in response
    assert response["statusCode"] == 200
    
    # Parse response body
    body = json.loads(response["body"])
    
    # Verify the response content
    assert "message" in body
    assert body["message"] == "Hello from Nexus!"
    assert "version" in body
    assert body["version"] == "1.0.0"


def test_lambda_handler_error(lambda_context, monkeypatch):
    """Test that the lambda_handler handles errors properly."""
    # Create a broken event
    broken_event = {"broken": True}
    
    # Monkeypatch the resolver to raise an exception
    def mock_resolve(*args, **kwargs):
        raise Exception("Test exception")
    
    # Apply the monkeypatch
    from nexus.functions.hello_world.app import app
    monkeypatch.setattr(app, "resolve", mock_resolve)
    
    # Call the lambda function
    response = lambda_handler(broken_event, lambda_context)
    
    # Verify the error response
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert "message" in body
    assert body["message"] == "Internal server error" 