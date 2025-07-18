#!/bin/bash

echo "Killing all Python and uvicorn processes..."
pkill -9 -f python
pkill -9 -f uvicorn

echo "Waiting for processes to terminate..."
sleep 3

echo "Starting fresh server..."
cd /Users/arosenkoetter/Sites/RavVitals/rayvitals-backend

# Option 1: Try using the Python in your PATH that has uvicorn
if command -v uvicorn &> /dev/null; then
    echo "Using uvicorn from PATH..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Option 2: Try the specific Python path that had uvicorn before
elif [ -f "/Users/arosenkoetter/Library/Python/3.12/bin/uvicorn" ]; then
    echo "Using uvicorn from user Python 3.12..."
    /Users/arosenkoetter/Library/Python/3.12/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Option 3: Try system Python 3
elif command -v python3 &> /dev/null; then
    echo "Trying with python3..."
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "ERROR: Could not find uvicorn!"
    echo ""
    echo "To fix this, try one of these options:"
    echo "1. Install uvicorn in Anaconda: conda install -c conda-forge uvicorn"
    echo "2. Or: pip install uvicorn"
    echo "3. Or use the specific path: /Users/arosenkoetter/Library/Python/3.12/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
fi