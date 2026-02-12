#!/bin/bash

echo "Starting UDTS Stock Analyzer Frontend..."
echo ""

cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies... (this may take a few minutes)"
    npm install
fi

# Start the frontend
echo ""
echo "Frontend will run on http://localhost:3000"
echo ""
npm start
