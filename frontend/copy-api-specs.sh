#!/bin/bash

# This script copies OpenAPI specs from services to frontend for API generation

# Create directory for API specs if it doesn't exist
mkdir -p src/lib/api/specs

# Copy specs from services
echo "Copying API specs from services..."

# Accounts service
if [ -f "../services/accounts/api/accounts.openapi.yaml" ]; then
  cp "../services/accounts/api/accounts.openapi.yaml" "src/lib/api/specs/accounts.yaml"
  echo "Copied accounts API spec"
else
  echo "Accounts API spec not found"
fi

# Workspaces service
if [ -f "../services/workspaces/api/workspaces.openapi.yaml" ]; then
  cp "../services/workspaces/api/workspaces.openapi.yaml" "src/lib/api/specs/workspaces.yaml"
  echo "Copied workspaces API spec"
else
  echo "Workspaces API spec not found"
fi

# Tasks service
if [ -f "../services/tasks/api/tasks.openapi.yaml" ]; then
  cp "../services/tasks/api/tasks.openapi.yaml" "src/lib/api/specs/tasks.yaml"
  echo "Copied tasks API spec"
else
  echo "Tasks API spec not found"
fi

# Comments service
if [ -f "../services/comments/api/comments.openapi.yaml" ]; then
  cp "../services/comments/api/comments.openapi.yaml" "src/lib/api/specs/comments.yaml"
  echo "Copied comments API spec"
else
  echo "Comments API spec not found"
fi

# Main OpenAPI spec
if [ -f "../services/api_docs/openapi.yaml" ]; then
  cp "../services/api_docs/openapi.yaml" "src/lib/api/specs/main.yaml"
  echo "Copied main API spec"
else
  echo "Main API spec not found"
fi

echo "API specs copied successfully!" 