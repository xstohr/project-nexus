#!/bin/bash

# This script installs all required dependencies for the API integration

# Install main dependencies
npm install @reduxjs/toolkit@^2.0.1 react-redux@^9.0.4 @tanstack/react-query@^4.36.1

# Install dev dependencies
npm install --save-dev orval@^6.23.0

echo "Dependencies installed successfully!" 