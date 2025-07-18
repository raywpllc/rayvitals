#!/bin/bash

# Kill any existing uvicorn processes
pkill -f "uvicorn.*main:app" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Set Python path
export PATH="/Users/arosenkoetter/Library/Python/3.12/bin:$PATH"

# Start the server
echo "Starting RayVitals backend server on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000