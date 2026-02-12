#!/bin/bash

echo "Starting UDTS Stock Analyzer Backend..."
echo ""

cd backend

# Check if .env exists
if [ ! -f .env ]; then
    cp ../.env .env
    echo "Copied .env file to backend directory"
fi

# Start the backend server
echo "Backend will run on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
python3 server.py
