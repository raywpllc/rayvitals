#!/usr/bin/env python3
"""
Complete deployment workflow: commit to GitHub and deploy to DigitalOcean
"""

import subprocess
import sys
import os
import time

def run_script(script_name):
    """Run a Python script and return success status"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=300)
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
    print("=== COMPLETE DEPLOYMENT WORKFLOW ===")
    print("This will commit all changes and deploy to DigitalOcean\n")
    
    # Change to the correct directory
    os.chdir("/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend")
    
    # Step 1: Commit changes to GitHub
    print("1. Committing changes to GitHub...")
    if not run_script("commit_changes.py"):
        print("❌ Failed to commit changes to GitHub")
        return False
    
    print("\n✅ Changes committed to GitHub successfully!")
    
    # Step 2: Deploy to DigitalOcean
    print("\n2. Deploying to DigitalOcean...")
    if not run_script("deploy_to_digitalocean.py"):
        print("❌ Deployment preparation failed")
        return False
    
    print("\n✅ Deployment initiated!")
    
    # Step 3: Summary
    print("\n" + "="*50)
    print("DEPLOYMENT SUMMARY")
    print("="*50)
    print("✅ All location tracking changes committed to GitHub")
    print("✅ DigitalOcean deployment initiated")
    print("✅ Production URL: https://rayvitals-backend-xwq86.ondigitalocean.app")
    print("\n📋 WHAT WAS DEPLOYED:")
    print("- Enhanced all scanners with detailed location tracking")
    print("- Each issue now includes URL, CSS selector, HTML snippet")
    print("- Severity levels and help text for all issues")
    print("- Improved AI summaries (less harsh, more constructive)")
    print("- Better 403 error handling across all scanners")
    print("- Structured issue format for easier debugging")
    print("\n⏱️  Deployment typically takes 5-10 minutes")
    print("🌐 Monitor at: https://cloud.digitalocean.com/apps")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)