#!/usr/bin/env python3
"""
Commit all changes to GitHub
"""

import subprocess
import sys
import os

def run_git_command(cmd):
    """Run git command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend')
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
    print("=== Committing Changes to GitHub ===")
    
    # Check git status
    print("\n1. Checking git status...")
    if not run_git_command("git status"):
        print("Failed to check git status")
        return False
    
    # Add all changes
    print("\n2. Adding all changes...")
    if not run_git_command("git add ."):
        print("Failed to add changes")
        return False
    
    # Check what will be committed
    print("\n3. Checking what will be committed...")
    if not run_git_command("git diff --cached --name-only"):
        print("Failed to check staged changes")
        return False
    
    # Commit with message
    commit_message = """Add comprehensive location tracking to all audit scanners

- Enhanced all scanners (security, performance, SEO, accessibility, UX) to include detailed location information
- Each issue now includes: URL, CSS selector, HTML snippet, severity level, and help text
- Updated AI analyzer to be less harsh and more constructive
- Fixed 403 error handling across all scanners
- Added structured issue format for better debugging and fixing
- Location tracking enables users to easily find and fix issues on their websites

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
    
    print("\n4. Committing changes...")
    if not run_git_command(f'git commit -m "{commit_message}"'):
        print("Failed to commit changes")
        return False
    
    # Push to GitHub
    print("\n5. Pushing to GitHub...")
    if not run_git_command("git push origin main"):
        print("Failed to push to GitHub")
        return False
    
    print("\n✅ Successfully committed and pushed all changes to GitHub!")
    
    # Show recent commits
    print("\n6. Recent commits:")
    run_git_command("git log --oneline -5")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)