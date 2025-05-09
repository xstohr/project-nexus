#!/bin/bash

# Run tests for Tasks service
echo "Running Tasks service tests..."

# Navigate to the service directory if not already there
cd "$(dirname "$0")" || exit

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Install test dependencies if needed
pip install -r requirements-test.txt --quiet

# Run tests with pytest
pytest -xvs tests/

echo "Tests completed!" 