#!/bin/bash
set -e

echo "==========================================="
echo "Starting PDFtoJSON application with Oracle"
echo "==========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Create a .env file com as variáveis de conexão TCP:"
    echo "ORACLE_USER=ADMIN"
    echo "ORACLE_PASSWORD=YourPassword"
    echo "ORACLE_DSN=host:port/service_name"
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