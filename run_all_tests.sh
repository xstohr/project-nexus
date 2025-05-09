#!/bin/bash
set -e

# Script to run tests for all services
echo "Running tests for all services..."

# Track overall success
OVERALL_SUCCESS=0

# Go through each service directory and run its tests if available
for SERVICE_DIR in services/*/; do
  SERVICE_NAME=$(basename $SERVICE_DIR)
  
  # Check if the service has a run_tests.sh script
  if [[ -f "$SERVICE_DIR/run_tests.sh" ]]; then
    echo "----------------------------------------"
    echo "Running tests for $SERVICE_NAME service"
    echo "----------------------------------------"
    
    # Go to the service directory and run its tests
    cd $SERVICE_DIR
    if bash ./run_tests.sh; then
      echo "✅ $SERVICE_NAME service tests passed"
    else
      echo "❌ $SERVICE_NAME service tests failed"
      OVERALL_SUCCESS=1
    fi
    
    # Go back to root directory
    cd ../../
    echo ""
  else
    echo "⚠️  No tests found for $SERVICE_NAME service (missing run_tests.sh)"
  fi
done

# Show summary
echo "----------------------------------------"
echo "Test Summary"
echo "----------------------------------------"
if [[ $OVERALL_SUCCESS -eq 0 ]]; then
  echo "✅ All tests passed successfully"
else
  echo "❌ Some tests failed, please check the output above"
fi

exit $OVERALL_SUCCESS 