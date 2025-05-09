#!/bin/bash
set -e  # Exit on error

# Check if environment is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <environment> [stack-name] [s3-bucket]"
  echo "  environment: dev, staging, or prod"
  echo "  stack-name: (optional) CloudFormation stack name (default: nexus-<environment>)"
  echo "  s3-bucket: (optional) S3 bucket for deployment artifacts (default: nexus-sam-<environment>)"
  exit 1
fi

# Set variables
ENV=$1
STACK_NAME=${2:-nexus-$ENV}
S3_BUCKET=${3:-nexus-sam-$ENV}
REGION=${AWS_REGION:-us-east-1}

echo "========================================"
echo "Deploying Nexus to environment: $ENV"
echo "Stack name: $STACK_NAME"
echo "S3 Bucket: $S3_BUCKET"
echo "Region: $REGION"
echo "========================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
  echo "AWS CLI is not installed. Please install it first."
  exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
  echo "AWS SAM CLI is not installed. Please install it first."
  exit 1
fi

# Create S3 bucket if it doesn't exist
if ! aws s3 ls "s3://$S3_BUCKET" &> /dev/null; then
  echo "Creating S3 bucket: $S3_BUCKET"
  aws s3 mb "s3://$S3_BUCKET" --region "$REGION"
fi

# Build the SAM application
echo "Building the SAM application..."
sam build

# Deploy the SAM application
echo "Deploying the SAM application..."
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --s3-bucket "$S3_BUCKET" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides "Environment=$ENV" \
  --region "$REGION" \
  --no-fail-on-empty-changeset

echo "========================================"
echo "Deployment completed successfully!"
echo "========================================"

# Get the API Gateway URL
API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text --region "$REGION")
echo "API Gateway URL: $API_URL"

# Get the Cognito User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --region "$REGION")
echo "Cognito User Pool ID: $USER_POOL_ID"

# Get the Cognito User Pool Client ID
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --region "$REGION")
echo "Cognito User Pool Client ID: $CLIENT_ID" 