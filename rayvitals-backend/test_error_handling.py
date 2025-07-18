#!/usr/bin/env python3
"""
Test error handling for problematic URLs
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner

async def test_error_handling():
    print("🔍 Testing Error Handling...")
    
    # Test URLs that might cause issues
    test_urls = [
        "https://example.com",  # Might return 403
        "https://httpbin.org/html",  # Should work
        "https://httpbin.org/status/404",  # 404 error
        "https://httpbin.org/status/403",  # 403 error
    ]
    
    for url in test_urls:
        print(f"\n🌐 Testing URL: {url}")
        
        # Test accessibility scanner
        print("   ♿ Accessibility Scanner...")
        accessibility_scanner = AccessibilityScanner()
        try:
            a11y_results = await accessibility_scanner.scan_website(url)
            print(f"      Score: {a11y_results.get('score', 0)}")
            print(f"      Issues: {len(a11y_results.get('issues', []))}")
            if a11y_results.get('issues'):
                print(f"      First issue: {a11y_results['issues'][0]}")
        except Exception as e:
            print(f"      Error: {e}")
        
        # Test UX scanner
        print("   👥 UX Scanner...")
        ux_scanner = UXScanner()
        try:
            ux_results = await ux_scanner.scan_website(url)
            print(f"      Score: {ux_results.get('score', 0)}")
            print(f"      Issues: {len(ux_results.get('issues', []))}")
            if ux_results.get('issues'):
                print(f"      First issue: {ux_results['issues'][0]}")
        except Exception as e:
            print(f"      Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_error_handling())