"""Resources Lambda function for the Nexus API."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import parse_qs
from aws_lambda_powertools.utilities.validation import validate_event
import boto3
from botocore.exceptions import ClientError

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("DYNAMODB_TABLE", "nexus-resources-dev")
table = dynamodb.Table(table_name)


@app.get("/resources")
def get_resources():
    """Get all resources."""
    # Parse query parameters
    query_params = app.current_event.query_string_parameters or {}
    limit = int(query_params.get("limit", "50"))
    next_token = query_params.get("next_token")
    
    # Build scan parameters
    scan_params = {
        "Limit": limit
    }
    
    if next_token:
        scan_params["ExclusiveStartKey"] = {"id": next_token}
    
    # Scan the table
    try:
        response = table.scan(**scan_params)
        items = response.get("Items", [])
        
        # Build the result
        result = {
            "items": items,
            "count": response.get("Count", 0),
        }
        
        # Add next token if available
        if "LastEvaluatedKey" in response:
            result["next_token"] = response["LastEvaluatedKey"]["id"]
        
        return result
    except ClientError as e:
        logger.exception("Error scanning resources")
        return app.response_builder(
            500,
            {"message": "Error fetching resources", "error": str(e)}
        )


@app.post("/resources")
def create_resource():
    """Create a new resource."""
    try:
        # Get the request body
        body = app.current_event.json_body
        
        # Generate an ID if not provided
        if "id" not in body:
            body["id"] = str(uuid.uuid4())
        
        # Add timestamps
        now = datetime.utcnow().isoformat()
        body["created_at"] = now
        body["updated_at"] = now
        
        # Ensure resource_type is provided
        if "resource_type" not in body:
            return app.response_builder(
                400,
                {"message": "resource_type is required"}
            )
        
        # Save to DynamoDB
        table.put_item(Item=body)
        
        return app.response_builder(201, body)
    except Exception as e:
        logger.exception("Error creating resource")
        return app.response_builder(
            500,
            {"message": "Error creating resource", "error": str(e)}
        )


@app.get("/resources/<id>")
def get_resource(id: str):
    """Get a resource by ID."""
    try:
        # Get the resource from DynamoDB
        response = table.get_item(Key={"id": id})
        item = response.get("Item")
        
        if not item:
            return app.response_builder(
                404,
                {"message": f"Resource with ID {id} not found"}
            )
        
        return item
    except Exception as e:
        logger.exception(f"Error getting resource {id}")
        return app.response_builder(
            500,
            {"message": f"Error getting resource {id}", "error": str(e)}
        )


@app.put("/resources/<id>")
def update_resource(id: str):
    """Update a resource."""
    try:
        # Check if the resource exists
        response = table.get_item(Key={"id": id})
        if "Item" not in response:
            return app.response_builder(
                404,
                {"message": f"Resource with ID {id} not found"}
            )
        
        # Get the request body
        body = app.current_event.json_body
        
        # Update the resource with the new data
        body["id"] = id  # Ensure ID doesn't change
        body["created_at"] = response["Item"].get("created_at")  # Preserve creation time
        body["updated_at"] = datetime.utcnow().isoformat()  # Update the updated_at timestamp
        
        # Save to DynamoDB
        table.put_item(Item=body)
        
        return body
    except Exception as e:
        logger.exception(f"Error updating resource {id}")
        return app.response_builder(
            500,
            {"message": f"Error updating resource {id}", "error": str(e)}
        )


@app.delete("/resources/<id>")
def delete_resource(id: str):
    """Delete a resource."""
    try:
        # Delete the resource
        response = table.delete_item(
            Key={"id": id},
            ReturnValues="ALL_OLD"
        )
        
        # Check if the resource existed
        if "Attributes" not in response:
            return app.response_builder(
                404,
                {"message": f"Resource with ID {id} not found"}
            )
        
        return app.response_builder(
            200,
            {"message": f"Resource with ID {id} deleted successfully"}
        )
    except Exception as e:
        logger.exception(f"Error deleting resource {id}")
        return app.response_builder(
            500,
            {"message": f"Error deleting resource {id}", "error": str(e)}
        )


def response_builder(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build a response with the given status code and body."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    """Lambda handler for the resources endpoint."""
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Unhandled error in resources Lambda")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error",
                "error": str(e)
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        } 