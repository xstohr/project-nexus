"""Authentication Lambda function for the Nexus app."""

import json
import os
import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Initialize Cognito client
cognito_idp = boto3.client('cognito-idp')
user_pool_id = os.environ.get('USER_POOL_ID')
app_client_id = os.environ.get('APP_CLIENT_ID')


@app.post("/auth/register")
def register():
    """Register a new user."""
    try:
        # Get request body
        body = app.current_event.json_body
        
        # Required fields
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        
        # Validate required fields
        if not email or not password or not name:
            return app.response_builder(
                400, 
                {"message": "Email, password, and name are required"}
            )
        
        # Create user in Cognito
        response = cognito_idp.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'name',
                    'Value': name
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                }
            ],
            MessageAction='SUPPRESS'  # Don't send email
        )
        
        # Set the password permanently
        cognito_idp.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        # Return success
        user_sub = next((attr['Value'] for attr in response['User']['Attributes'] 
                        if attr['Name'] == 'sub'), None)
        
        return {
            "message": "User registered successfully",
            "user_id": user_sub,
            "username": email
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        
        if error_code == 'UsernameExistsException':
            return app.response_builder(
                409, 
                {"message": "A user with this email already exists"}
            )
        
        logger.exception("Error registering user")
        return app.response_builder(
            500,
            {"message": "Error registering user", "error": str(e)}
        )


@app.post("/auth/login")
def login():
    """Log in a user."""
    try:
        # Get request body
        body = app.current_event.json_body
        
        # Required fields
        email = body.get('email')
        password = body.get('password')
        
        # Validate required fields
        if not email or not password:
            return app.response_builder(
                400,
                {"message": "Email and password are required"}
            )
        
        # Authenticate the user
        response = cognito_idp.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=app_client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        # Return tokens
        auth_result = response.get('AuthenticationResult', {})
        return {
            "access_token": auth_result.get('AccessToken'),
            "id_token": auth_result.get('IdToken'),
            "refresh_token": auth_result.get('RefreshToken'),
            "expires_in": auth_result.get('ExpiresIn'),
            "token_type": auth_result.get('TokenType')
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        
        if error_code == 'NotAuthorizedException':
            return app.response_builder(
                401,
                {"message": "Invalid username or password"}
            )
        
        if error_code == 'UserNotFoundException':
            return app.response_builder(
                404,
                {"message": "User not found"}
            )
        
        logger.exception("Error logging in user")
        return app.response_builder(
            500,
            {"message": "Error logging in user", "error": str(e)}
        )


@app.get("/auth/user")
def get_user():
    """Get user information."""
    try:
        # Get the authorization header
        auth_header = app.current_event.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return app.response_builder(
                401,
                {"message": "Missing or invalid authorization token"}
            )
        
        # Extract the access token
        access_token = auth_header.split(' ')[1]
        
        # Get the user from Cognito
        response = cognito_idp.get_user(
            AccessToken=access_token
        )
        
        # Extract user attributes
        user_attributes = {
            attr['Name']: attr['Value'] 
            for attr in response['UserAttributes']
        }
        
        # Return user data
        return {
            "user_id": user_attributes.get('sub'),
            "email": user_attributes.get('email'),
            "name": user_attributes.get('name'),
            "email_verified": user_attributes.get('email_verified') == 'true'
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        
        if error_code == 'NotAuthorizedException':
            return app.response_builder(
                401,
                {"message": "Invalid or expired token"}
            )
        
        logger.exception("Error getting user information")
        return app.response_builder(
            500,
            {"message": "Error getting user information", "error": str(e)}
        )


def response_builder(status_code: int, body: dict) -> dict:
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
    """Lambda handler for the authentication endpoints."""
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Unhandled error in authentication Lambda")
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