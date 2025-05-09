#!/bin/bash
set -e

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..

# Install dev dependencies if needed
pip install -r requirements-dev.txt

# Run tests with coverage
pytest tests/ \
  --cov=functions/ \
  --cov-report=term \
  --cov-report=html:coverage_report/ \
  -v

echo "Test coverage report generated in coverage_report/" 