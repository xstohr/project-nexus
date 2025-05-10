#!/bin/bash

# This script generates API code from OpenAPI specs

# Step 1: Copy API specs from services
echo "Copying API specs from services..."
./copy-api-specs.sh

# Step 2: Run Orval to generate API code
echo "Generating API code..."
npx orval

echo "API code generation completed!" 