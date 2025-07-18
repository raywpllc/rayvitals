#!/usr/bin/env python3
"""
Test script to verify location tracking is working for all scanners
"""

import requests
import json
import time

def test_location_tracking():
    print("Testing location tracking in all scanners...")
    
    # Use the demo endpoint to test all scanners
    url = "http://localhost:8000/api/v1/audit/demo"
    data = {"url": "https://tailfin.com"}
    
    try:
        print("Sending request to demo endpoint...")
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        print(f"Response status: {response.status_code}")
        
        # Check each scanner for location tracking
        scanners = ["security", "performance", "seo", "accessibility", "ux"]
        
        for scanner_name in scanners:
            print(f"\n=== {scanner_name.upper()} SCANNER ===")
            scanner_data = result.get("results", {}).get(scanner_name, {})
            
            if not scanner_data:
                print(f"No data found for {scanner_name}")
                continue
                
            issues = scanner_data.get("issues", [])
            print(f"Found {len(issues)} issues")
            
            if issues:
                # Check first issue for location tracking
                first_issue = issues[0]
                print(f"First issue: {first_issue}")
                
                if isinstance(first_issue, dict) and "location" in first_issue:
                    location = first_issue["location"]
                    print(f"✅ Location tracking found:")
                    print(f"  - URL: {location.get('url', 'N/A')}")
                    print(f"  - Selector: {location.get('selector', 'N/A')}")
                    print(f"  - HTML snippet: {location.get('html_snippet', 'N/A')}")
                    print(f"  - Severity: {first_issue.get('severity', 'N/A')}")
                    print(f"  - Help: {first_issue.get('help', 'N/A')}")
                else:
                    print(f"❌ Location tracking NOT found - issue format: {type(first_issue)}")
            else:
                print(f"No issues found for {scanner_name}")
        
        # Save full response for inspection
        with open("location_tracking_test_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull response saved to location_tracking_test_response.json")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_location_tracking()