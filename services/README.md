# Nexus Services

This directory contains the microservices that make up the Nexus application.

## Service Architecture

Nexus follows a microservices architecture within a monorepo structure. Each service:

1. Has its own subdirectory
2. Has a clear, single responsibility
3. Includes its own Lambda functions, models, and business logic
4. Shares common utilities from the main nexus package

## Services

### API Service

Handles all HTTP API requests, manages API Gateway integration, and routes requests to appropriate services.

### Resource Service

Manages the core resources of the application, handles CRUD operations, and enforces business rules.

### Auth Service

Handles authentication, authorization, and user management.

### Analytics Service

Collects and processes analytics data.

## Deployment

Each service can be deployed independently using AWS SAM, or all services can be deployed together.

```
# Deploy all services
cd nexus
sam build
sam deploy

# Deploy a specific service
cd nexus/services/api
sam build -t template.yaml
sam deploy --stack-name nexus-api
``` 