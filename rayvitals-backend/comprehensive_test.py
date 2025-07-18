#!/usr/bin/env python3
"""
Comprehensive test for location tracking and server functionality
"""

import subprocess
import sys
import time
import os

def run_script(script_name):
    """Run a Python script and return success status"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=30)
        print(f"=== {script_name} OUTPUT ===")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    print("=== COMPREHENSIVE TEST SUITE ===")
    
    # Change to the correct directory
    os.chdir("/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend")
    
    # Step 1: Check server health and start if needed
    print("\n1. Checking server health...")
    if not run_script("test_server_health.py"):
        print("❌ Server health check failed")
        return False
    
    # Step 2: Wait a bit for server to fully start
    print("\n2. Waiting for server to fully initialize...")
    time.sleep(10)
    
    # Step 3: Test location tracking
    print("\n3. Testing location tracking...")
    if not run_script("test_location_tracking.py"):
        print("❌ Location tracking test failed")
        return False
    
    print("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)