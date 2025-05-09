import json
import os
import logging
import boto3
import yaml
import base64

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Initialize boto3 client
s3 = boto3.client('s3')

# Constants
BUCKET_NAME = os.environ.get('API_DOCS_BUCKET', 'nexus-api-docs-dev')
DEFAULT_OPENAPI_PATH = 'openapi.yaml'

# HTML template for Swagger UI
SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { background-color: #222; }
        .swagger-ui .info .title { color: #333; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{url}",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout"
            });
            window.ui = ui;
        };
    </script>
</body>
</html>
"""

def lambda_handler(event, context):
    """
    Lambda handler for the Swagger UI
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get the path from the event
    path = event.get('path', '/')
    
    try:
        if path == '/' or path == '/docs':
            # Return Swagger UI HTML
            api_url = f"/openapi.json"
            html_content = SWAGGER_UI_HTML.replace("{url}", api_url)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': html_content
            }
        
        elif path == '/openapi.yaml':
            # Return OpenAPI spec in YAML format
            try:
                # Try to get from S3 first
                response = s3.get_object(Bucket=BUCKET_NAME, Key=DEFAULT_OPENAPI_PATH)
                yaml_content = response['Body'].read().decode('utf-8')
            except Exception as e:
                logger.warning(f"Error retrieving from S3: {str(e)}")
                # If not in S3, read from local file
                with open(os.path.join(os.path.dirname(__file__), '../../openapi.yaml'), 'r') as f:
                    yaml_content = f.read()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/yaml',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': yaml_content
            }
        
        elif path == '/openapi.json':
            # Return OpenAPI spec in JSON format
            try:
                # Try to get from S3 first
                response = s3.get_object(Bucket=BUCKET_NAME, Key=DEFAULT_OPENAPI_PATH)
                yaml_content = response['Body'].read().decode('utf-8')
            except Exception as e:
                logger.warning(f"Error retrieving from S3: {str(e)}")
                # If not in S3, read from local file
                with open(os.path.join(os.path.dirname(__file__), '../../openapi.yaml'), 'r') as f:
                    yaml_content = f.read()
            
            # Convert YAML to JSON
            json_content = json.dumps(yaml.safe_load(yaml_content))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json_content
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Not Found'
                })
            }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Internal Server Error',
                'error': str(e)
            })
        } 