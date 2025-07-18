#!/usr/bin/env python3
"""
Simple test to verify scanners work locally
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner

async def test_scanners():
    print("🔍 Testing RayVitals Scanners...")
    
    # Test URL
    url = "https://httpbin.org/html"
    print(f"Testing URL: {url}")
    
    # Test accessibility scanner
    print("\n♿ Testing Accessibility Scanner...")
    accessibility_scanner = AccessibilityScanner()
    try:
        a11y_results = await accessibility_scanner.scan_website(url)
        print(f"   ✅ Accessibility Score: {a11y_results.get('score', 0)}")
        print(f"   Issues found: {len(a11y_results.get('issues', []))}")
    except Exception as e:
        print(f"   ❌ Accessibility scan failed: {e}")
    
    # Test UX scanner
    print("\n👥 Testing UX Scanner...")
    ux_scanner = UXScanner()
    try:
        ux_results = await ux_scanner.scan_website(url)
        print(f"   ✅ UX Score: {ux_results.get('score', 0)}")
        print(f"   Issues found: {len(ux_results.get('issues', []))}")
    except Exception as e:
        print(f"   ❌ UX scan failed: {e}")
    
    print("\n✅ Scanner test completed!")

if __name__ == "__main__":
    asyncio.run(test_scanners())