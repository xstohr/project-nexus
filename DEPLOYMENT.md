# Nexus Deployment Guide

This guide provides instructions for deploying the Nexus Project Management Platform using AWS Serverless Application Model (SAM).

## Prerequisites

Before you begin, ensure you have the following:

1. **AWS CLI**: Install and configure the [AWS Command Line Interface](https://aws.amazon.com/cli/)
2. **AWS SAM CLI**: Install the [AWS Serverless Application Model CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
3. **AWS Account**: Access to an AWS account with permissions to create resources
4. **Python 3.11**: Required for the Lambda runtime environment

## Deployment Process

Nexus provides a simplified deployment script that handles the AWS SAM build and deploy process.

### Using the Deployment Script

1. Make the script executable (if not already):
   ```bash
   chmod +x deploy.sh
   ```

2. Run the deployment script with the desired environment:
   ```bash
   ./deploy.sh dev
   ```

   Available environments:
   - `dev`: Development environment
   - `staging`: Staging/testing environment
   - `prod`: Production environment

   Optional parameters:
   ```bash
   ./deploy.sh <environment> <stack-name> <s3-bucket>
   ```
   - `stack-name`: CloudFormation stack name (default: nexus-<environment>)
   - `s3-bucket`: S3 bucket for deployment artifacts (default: nexus-sam-<environment>)

### Manual Deployment

If you prefer to deploy manually:

1. Build the application:
   ```bash
   sam build
   ```

2. Deploy the application:
   ```bash
   sam deploy \
     --stack-name nexus-dev \
     --s3-bucket your-deployment-bucket \
     --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
     --parameter-overrides Environment=dev \
     --region us-east-1
   ```

## Service Architecture

Nexus is built with a microservices architecture, consisting of several independent services:

- **Accounts Service**: User account management
- **Auth Service**: Authentication and authorization
- **Tasks Service**: Task management
- **Workspaces Service**: Workspace management
- **Comments Service**: Comment functionality
- **User Roles Service**: Role-based access control
- **Time Tracking Service**: Time entry tracking
- **API Service**: API Gateway integration

Each service is deployed as a nested CloudFormation stack.

## Deployment Resources

The deployment creates the following AWS resources:

- **Lambda Functions**: Serverless functions for each service
- **DynamoDB Tables**: NoSQL databases for data persistence
- **API Gateway**: REST API endpoints
- **Cognito User Pool**: User authentication
- **IAM Roles and Policies**: Fine-grained access control
- **CloudWatch Logs**: Application logging

## Post-Deployment

After successful deployment, the script will output:

- API Gateway URL
- Cognito User Pool ID
- Cognito User Pool Client ID

Save these values for client application configuration.

## Monitoring and Troubleshooting

- **CloudWatch Logs**: Each Lambda function logs to CloudWatch
- **CloudFormation Console**: Check stack status and resources
- **API Gateway Console**: Test and monitor API endpoints

## Cleanup

To delete all resources, run:

```bash
aws cloudformation delete-stack --stack-name nexus-dev --region us-east-1
```

Replace `nexus-dev` with your stack name and region as needed. 