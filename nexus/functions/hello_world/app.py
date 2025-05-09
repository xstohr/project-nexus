import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

@app.get("/hello")
def hello():
    return {
        "message": "Hello from Nexus!",
        "version": "1.0.0"
    }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Error handling request")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error",
                "error": str(e)
            })
        } 