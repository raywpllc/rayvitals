#!/usr/bin/env python3
"""
Test server health and start if needed
"""

import requests
import subprocess
import time
import sys

def check_server_health():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        return False

def start_server():
    """Try to start the server"""
    print("Attempting to start server...")
    
    # Kill existing processes
    try:
        subprocess.run(["pkill", "-9", "-f", "python"], check=False)
        subprocess.run(["pkill", "-9", "-f", "uvicorn"], check=False)
        time.sleep(2)
    except Exception as e:
        print(f"Warning: Could not kill processes: {e}")
    
    # Try different ways to start uvicorn
    commands = [
        ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        ["/Users/arosenkoetter/Library/Python/3.12/bin/uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        ["python3", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        ["python", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    ]
    
    for cmd in commands:
        try:
            print(f"Trying command: {' '.join(cmd)}")
            # Start the server in the background
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            time.sleep(5)
            
            # Check if it's working
            if check_server_health():
                print("✅ Server started successfully!")
                return True
            else:
                # Kill this attempt
                process.terminate()
                time.sleep(1)
                
        except Exception as e:
            print(f"Command failed: {e}")
    
    print("❌ Could not start server with any method")
    return False

def main():
    print("=== Server Health Check ===")
    
    if check_server_health():
        print("Server is already running")
        return True
    
    print("Server is not running, attempting to start...")
    return start_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)