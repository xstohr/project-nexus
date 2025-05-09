# Nexus Multi-Tenant Task Management System

A serverless multi-tenant task management platform built with AWS services, following a microservices architecture with Lambda functions, DynamoDB, and API Gateway.

## Architecture

The system is divided into separate services, each responsible for a specific domain:

1. **Accounts Service**: Manages account creation, account settings, and user membership
2. **Workspaces Service**: Handles workspace creation and management
3. **User Roles Service**: Controls role-based permissions
4. **Tasks Service**: Manages task creation, updates, assignment and status
5. **Comments Service**: Provides commenting functionality on tasks
6. **Time Tracking Service**: Tracks time spent on tasks
7. **Authentication Service**: Handles user authentication and authorization

Each service follows a modular design:

```
services/{service_name}/
├── api/                       # API definitions
│   └── {service}.openapi.yaml # OpenAPI specification
├── functions/                 # Lambda functions
│   ├── shared/                # Shared code
│   │   ├── models/            # Data models
│   │   └── utils/             # Utility functions
│   └── {domain}_operations/   # Domain operations
│       └── {operation}/       # Individual Lambda functions
├── tests/                     # Unit tests
└── template.yaml              # AWS SAM template
```

## Design Principles

1. **Modularity**: Each Lambda function is focused on a single responsibility
2. **Testability**: All functions are easy to test in isolation
3. **Reusability**: Common code is shared via utility modules
4. **Observability**: Structured logging and monitoring built-in
5. **Security**: Role-based access controls and tenant isolation

## Multi-Tenant Design

The system uses a pool isolation model with logical tenant separation:

- Data is stored in shared DynamoDB tables with tenant identifiers
- API Gateway routes requests to the correct Lambda functions
- Cognito handles authentication with tenant context in tokens
- A single-table design with GSIs enables efficient queries

## Available Services

### Accounts Service

Manages multi-tenant accounts, including:
- Account creation and management
- Tenant isolation
- User membership
- Role-based permissions

[View Accounts Service Documentation](services/accounts/README.md)

### Workspaces Service

Handles workspace management within accounts:
- Workspace creation and configuration
- User access management
- Workspace metadata

[View Workspaces Service Documentation](services/workspaces/README.md)

### Tasks Service

Manages the core task functionality:
- Task creation and updates
- Task assignment
- Status management
- Priority handling

[View Tasks Service Documentation](services/tasks/README.md)

### Comments Service

Provides commenting functionality:
- Task comments
- Comment threads
- User mentions
- Activity tracking

[View Comments Service Documentation](services/comments/README.md)

## Getting Started

### Prerequisites

- Python 3.11+
- AWS SAM CLI
- AWS CLI
- Docker (for local development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nexus.git
cd nexus
```

2. Install dependencies for local development:
```bash
pip install -r requirements-dev.txt
```

3. Deploy to AWS:
```bash
sam build
sam deploy --guided
```

### Running Tests

Each service contains its own test suite. To run all tests:

```bash
./run_all_tests.sh
```

Or to test an individual service:

```bash
cd services/{service_name}
./run_tests.sh
```

## API Documentation

Each service provides OpenAPI specifications in the `api/` directory.

## Contributing

1. Create a new branch for your feature
2. Follow the modular architecture pattern
3. Add unit tests for all new functionality
4. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
``` 