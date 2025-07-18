#!/bin/bash

echo "Killing all Python and uvicorn processes..."
pkill -9 -f python
pkill -9 -f uvicorn

echo "Waiting for processes to terminate..."
sleep 3

echo "Starting fresh server..."
cd /Users/arosenkoetter/Sites/RavVitals/rayvitals-backend
export PATH="/Users/arosenkoetter/Library/Python/3.12/bin:$PATH"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000