# Tasks Service

The Tasks service is a microservice component of the Nexus application that provides capabilities for managing tasks within a workspace.

## Features

- Create, read, update, and delete tasks
- List tasks with filtering and pagination
- Task properties include title, description, status, priority, assignee, due date, and tags
- Efficient querying by workspace, status, priority, and assignee

## Architecture

The service follows a modular design pattern with:

- **Lambda Functions**: Following single responsibility principle
- **DynamoDB**: For persistent storage with efficient access patterns
- **Shared Utilities**: Common code for authentication, response building, and database operations
- **Data Models**: Standardized data structures and validation
- **Tests**: Comprehensive unit tests for all components

## Directory Structure

```
services/tasks/
├── api/                       # API specification
│   └── tasks.openapi.yaml     # OpenAPI documentation
├── functions/                 # Lambda functions
│   ├── shared/                # Shared code across functions
│   │   ├── utils/             # Utility functions
│   │   └── models/            # Data models
│   └── task_operations/       # Task operations
│       ├── create_task/       # Create task function
│       ├── get_task/          # Get task function
│       ├── update_task/       # Update task function
│       ├── delete_task/       # Delete task function
│       └── list_tasks/        # List tasks function
├── tests/                     # Unit tests
│   ├── conftest.py            # Test fixtures
│   ├── test_create_task.py    # Tests for create task
│   ├── test_get_task.py       # Tests for get task
│   ├── test_update_task.py    # Tests for update task
│   ├── test_delete_task.py    # Tests for delete task
│   ├── test_list_tasks.py     # Tests for list tasks
│   ├── test_task_models.py    # Tests for task models
│   └── test_utils.py          # Tests for utilities
├── template.yaml              # AWS SAM template
├── requirements-test.txt      # Test dependencies
└── run_tests.sh               # Script to run tests
```

## Database Design

Tasks are stored in DynamoDB with the following structure:

- **Primary Key**: 
  - PK: `WORKSPACE#{workspace_id}`
  - SK: `TASK#{task_id}`
- **Global Secondary Index 1**:
  - GSI1PK: `WORKSPACE#{workspace_id}`
  - GSI1SK: `STATUS#{status}#PRIORITY#{priority}#TASK#{task_id}`
- **Global Secondary Index 2**:
  - GSI2PK: `WORKSPACE#{workspace_id}`
  - GSI2SK: `ASSIGNEE#{assignee_id}#TASK#{task_id}`

This design enables efficient queries by workspace, status, priority, and assignee.

## Testing

Run the tests using the provided script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Deployment

The service can be deployed using AWS SAM:

```bash
sam build -t template.yaml
sam deploy --guided
``` 