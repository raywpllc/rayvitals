#!/usr/bin/env python3
"""Test current SEO implementation"""

import requests
import json

url = "http://localhost:8000/api/v1/audit/demo"
data = {"url": "https://tailfin.com"}

print("Testing SEO scanner...")
response = requests.post(url, json=data)
result = response.json()

print("\nSEO Results:")
seo_data = result.get("results", {}).get("seo", {})
print(f"Score: {seo_data.get('score')}")
print(f"Issues: {seo_data.get('issues')}")
print(f"Recommendations: {seo_data.get('recommendations')}")

# Check if it's using the old or new implementation
if any("403" in str(issue) for issue in seo_data.get('issues', [])):
    print("\n❌ USING OLD IMPLEMENTATION - Server needs restart")
else:
    print("\n✅ Using new implementation")

# Save full response
with open("current_seo_response.json", "w") as f:
    json.dump(result, f, indent=2)
print("\nFull response saved to current_seo_response.json")