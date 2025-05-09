# Workspaces Service

This service manages workspaces within the Nexus platform, allowing users to create isolated environments for their tasks, comments, and team collaboration.

## Architecture

The service follows a modular, single-responsibility approach with each Lambda function dedicated to a specific operation. This ensures separation of concerns, easier testing, and more maintainable code.

### Directory Structure

```
services/workspaces/
├── api/
│   └── workspaces.openapi.yaml  # OpenAPI specification
├── functions/
│   ├── shared/                  # Shared utilities and models
│   │   ├── models/              # Data models
│   │   └── utils/               # Utility functions
│   └── workspace_operations/    # Lambda functions
│       ├── create_workspace/    # Create workspace function
│       ├── get_workspace/       # Get workspace function
│       ├── update_workspace/    # Update workspace function
│       ├── delete_workspace/    # Delete workspace function
│       └── list_workspaces/     # List workspaces function
├── tests/                       # Unit tests
│   ├── conftest.py              # Test configuration and fixtures
│   ├── test_*.py                # Test modules
└── template.yaml                # AWS SAM template
```

## API Endpoints

The service exposes the following RESTful endpoints:

- `POST /accounts/{accountId}/workspaces` - Create a new workspace
- `GET /accounts/{accountId}/workspaces` - List workspaces for an account
- `GET /workspaces/{workspaceId}` - Get workspace details
- `PUT /workspaces/{workspaceId}` - Update workspace details
- `DELETE /workspaces/{workspaceId}` - Delete (deactivate) a workspace

For detailed API documentation, see the OpenAPI specification in `api/workspaces.openapi.yaml`.

## Database Design

The service uses a DynamoDB table shared with the Accounts service, utilizing a single-table design pattern with the following key structure:

- **Primary Keys**:
  - `PK`: Partition key with patterns like `ACCOUNT#{accountId}` or `WORKSPACE#{workspaceId}`
  - `SK`: Sort key with patterns like `METADATA`, `WORKSPACE#{workspaceId}`, or `USER#{userId}`

- **Global Secondary Indexes**:
  - `GSI1`: For querying by user
    - `GSI1PK`: `USER#{userId}`
    - `GSI1SK`: `WORKSPACE#{workspaceId}`
  - `WorkspaceIdIndex`: For direct workspace lookups
    - `workspace_id`: The workspace ID

## Development

### Running Tests

To run the test suite with coverage reporting:

```bash
./run_tests.sh
```

### Adding a New Function

To add a new function:

1. Create a new directory under `functions/workspace_operations/`
2. Add the function logic in a Python module
3. Add the function definition to `template.yaml`
4. Create corresponding tests in the `tests/` directory

### Requirements

- Python 3.11
- AWS SAM CLI for local development
- Required Python packages listed in `requirements-dev.txt` 