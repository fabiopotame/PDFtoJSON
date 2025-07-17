#!/bin/bash
set -e

echo "==========================================="
echo "Running PDFtoJSON Unit Tests (Standalone)"
echo "==========================================="

# Check if we're in a Docker environment
if [ -f /.dockerenv ]; then
    echo "Running tests in Docker environment..."
    # In Docker, we don't need to check for .env file
    python3 -m unittest discover tests -v
else
    echo "Running tests in local environment..."
    
    # Check if .env file exists for local testing
    if [ ! -f .env ]; then
        echo "WARNING: .env file not found. Some tests may fail if they require database connection."
        echo "Create a .env file with Oracle settings for full test coverage."
    fi
    
    # Run tests
    python3 -m unittest discover tests -v
fi

echo "==========================================="
echo "Tests completed!"
echo "===========================================" 