"""Health check Lambda function for the Nexus API."""

import json
import os
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

@app.get("/health")
def health():
    """Health check endpoint for the Nexus API."""
    environment = os.environ.get("ENVIRONMENT", "unknown")
    
    # Return health status
    return {
        "status": "healthy",
        "service": "nexus-api",
        "environment": environment,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    """Lambda handler for the health check endpoint."""
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Error handling health check request")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": "Internal server error",
                "error": str(e)
            })
        } 