#!/usr/bin/env python3
"""
Simple script to start the server
"""

import subprocess
import sys
import time
import os

def main():
    print("=== Starting RayVitals Server ===")
    
    # Change to correct directory
    os.chdir("/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend")
    print(f"Current directory: {os.getcwd()}")
    
    # Kill any existing processes
    try:
        subprocess.run(["pkill", "-9", "-f", "uvicorn"], check=False)
        subprocess.run(["pkill", "-9", "-f", "python.*app.main"], check=False)
        print("Killed existing processes")
        time.sleep(2)
    except Exception as e:
        print(f"Warning killing processes: {e}")
    
    # Check if uvicorn is available
    try:
        result = subprocess.run(["which", "uvicorn"], capture_output=True, text=True)
        if result.returncode == 0:
            uvicorn_path = result.stdout.strip()
            print(f"Found uvicorn at: {uvicorn_path}")
        else:
            print("uvicorn not found in PATH")
    except Exception as e:
        print(f"Error checking uvicorn: {e}")
    
    # Try to start the server
    commands = [
        ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        ["python3", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        ["/Users/arosenkoetter/Library/Python/3.12/bin/uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    ]
    
    for i, cmd in enumerate(commands):
        try:
            print(f"\nTrying method {i+1}: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Started process with PID: {process.pid}")
            print("Server should be starting... Check http://localhost:8000/health")
            print("Press Ctrl+C to stop")
            
            # Keep the process running
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\nStopping server...")
                process.terminate()
                process.wait()
                
            return True
            
        except Exception as e:
            print(f"Method {i+1} failed: {e}")
            continue
    
    print("❌ All methods failed")
    return False

if __name__ == "__main__":
    main()