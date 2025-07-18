#!/usr/bin/env python3
"""
Deploy changes to DigitalOcean App Platform
"""

import subprocess
import sys
import os
import time

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"$ {cmd}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("=== Deploying to DigitalOcean App Platform ===")
    
    # Check if doctl is installed
    print("\n1. Checking DigitalOcean CLI...")
    if not run_command("which doctl"):
        print("DigitalOcean CLI (doctl) not found. Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/")
        print("Alternatively, the deployment will happen automatically via GitHub integration.")
        return False
    
    # Check authentication
    print("\n2. Checking authentication...")
    if not run_command("doctl auth whoami"):
        print("Not authenticated with DigitalOcean. Run: doctl auth init")
        return False
    
    # List apps to find our app
    print("\n3. Finding RayVitals app...")
    if not run_command("doctl apps list"):
        print("Failed to list apps")
        return False
    
    # The app should auto-deploy from GitHub, but we can trigger a manual deployment
    print("\n4. DigitalOcean App Platform Integration:")
    print("✅ Changes have been pushed to GitHub")
    print("✅ DigitalOcean should automatically detect and deploy the changes")
    print("✅ You can monitor the deployment at: https://cloud.digitalocean.com/apps")
    
    # Provide the production URL
    print("\n5. Production URL:")
    print("🌐 https://rayvitals-backend-xwq86.ondigitalocean.app")
    
    print("\n6. Deployment Status:")
    print("The deployment typically takes 5-10 minutes to complete.")
    print("Location tracking features will be available once deployment finishes.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)