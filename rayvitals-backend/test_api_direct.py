#!/usr/bin/env python3
"""Direct API test to verify the demo endpoint"""

import requests
import json

def test_demo_endpoint():
    url = "http://localhost:8000/api/v1/audit/demo"
    data = {"url": "https://tailfin.com"}
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        print("Status Code:", response.status_code)
        print("\nScores:")
        for key, value in result.get("scores", {}).items():
            print(f"  {key}: {value}")
        
        print("\nCategories in results:")
        for category in result.get("results", {}).keys():
            print(f"  - {category}")
            
        print("\nSecurity Headers Score:", result.get("results", {}).get("security", {}).get("security_headers", {}).get("score"))
        
        # Save full response for inspection
        with open("test_api_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nFull response saved to test_api_response.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_demo_endpoint()