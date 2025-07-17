#!/bin/bash
set -e

echo "==========================================="
echo "Starting PDFtoJSON application with Oracle"
echo "==========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Create a .env file with Oracle settings:"
    echo "ORACLE_USERNAME=ADMIN"
    echo "ORACLE_PASSWORD=YourPassword"
    echo "ORACLE_SERVICE_NAME=nh66vvfwukxku4dc_high"
    exit 1
fi

# Execute database initialization
echo "Executing database initialization..."
python3 scripts/init_database.py

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "Database initialized successfully!"
else
    echo "ERROR: Database initialization failed"
    exit 1
fi

echo "Starting Flask application..."
python3 app.py 