#!/usr/bin/env python3
"""
Complete audit test with all scanners
"""

import asyncio
import sys
import os
import json
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.security_scanner import SecurityScanner
from app.services.performance_scanner import PerformanceScanner
from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner

async def run_complete_audit(url):
    """Run complete audit with all scanners"""
    print(f"\n🔍 Starting Complete Audit for: {url}")
    print("=" * 60)
    
    start_time = time.time()
    audit_results = {}
    
    # Security Scanner
    print("🔒 Running Security Scanner...")
    security_scanner = SecurityScanner()
    try:
        security_results = await security_scanner.scan_website(url)
        audit_results["security"] = security_results
        print(f"   ✅ Security Score: {security_results.get('score', 0)}")
    except Exception as e:
        print(f"   ❌ Security scan failed: {e}")
        audit_results["security"] = {"score": 0, "issues": [f"Security scan failed: {e}"]}
    
    # Performance Scanner
    print("⚡ Running Performance Scanner...")
    performance_scanner = PerformanceScanner()
    try:
        performance_results = await performance_scanner.scan_website(url)
        audit_results["performance"] = performance_results
        print(f"   ✅ Performance Score: {performance_results.get('score', 0)}")
    except Exception as e:
        print(f"   ❌ Performance scan failed: {e}")
        audit_results["performance"] = {"score": 0, "issues": [f"Performance scan failed: {e}"]}
    
    # Accessibility Scanner
    print("♿ Running Accessibility Scanner...")
    accessibility_scanner = AccessibilityScanner()
    try:
        accessibility_results = await accessibility_scanner.scan_website(url)
        audit_results["accessibility"] = accessibility_results
        print(f"   ✅ Accessibility Score: {accessibility_results.get('score', 0)}")
    except Exception as e:
        print(f"   ❌ Accessibility scan failed: {e}")
        audit_results["accessibility"] = {"score": 0, "issues": [f"Accessibility scan failed: {e}"]}
    
    # UX Scanner
    print("👥 Running UX Scanner...")
    ux_scanner = UXScanner()
    try:
        ux_results = await ux_scanner.scan_website(url)
        audit_results["ux"] = ux_results
        print(f"   ✅ UX Score: {ux_results.get('score', 0)}")
    except Exception as e:
        print(f"   ❌ UX scan failed: {e}")
        audit_results["ux"] = {"score": 0, "issues": [f"UX scan failed: {e}"]}
    
    # Calculate overall score
    scores = {
        "security": audit_results.get("security", {}).get("score", 0),
        "performance": audit_results.get("performance", {}).get("score", 0),
        "accessibility": audit_results.get("accessibility", {}).get("score", 0),
        "ux": audit_results.get("ux", {}).get("score", 0),
    }
    
    # Weighted overall score
    weights = {"security": 0.25, "performance": 0.25, "accessibility": 0.2, "ux": 0.3}
    overall_score = sum(scores[category] * weights[category] for category in scores)
    scores["overall"] = round(overall_score, 1)
    
    processing_time = time.time() - start_time
    
    # Display results
    print(f"\n🎯 AUDIT RESULTS")
    print("=" * 60)
    print(f"Overall Score: {scores['overall']}")
    print(f"Security: {scores['security']}")
    print(f"Performance: {scores['performance']}")
    print(f"Accessibility: {scores['accessibility']}")
    print(f"UX: {scores['ux']}")
    print(f"Processing Time: {processing_time:.2f}s")
    
    # Show summary of issues
    print(f"\n📋 ISSUE SUMMARY")
    print("=" * 60)
    for category, results in audit_results.items():
        issues = results.get("issues", [])
        if issues:
            print(f"{category.upper()}: {len(issues)} issues")
            for issue in issues[:2]:  # Show first 2 issues
                print(f"   • {issue}")
            if len(issues) > 2:
                print(f"   ... and {len(issues) - 2} more")
    
    return {
        "url": url,
        "scores": scores,
        "results": audit_results,
        "processing_time": processing_time
    }

async def main():
    """Main test function"""
    print("🎯 RayVitals Complete Audit Test")
    print("=" * 60)
    
    # Test URLs
    test_urls = [
        "https://httpbin.org/html",  # Should work well
        "https://example.com",       # Basic test
    ]
    
    for url in test_urls:
        try:
            result = await run_complete_audit(url)
            
            # Option to save results
            print(f"\n💾 Saving results for {url}")
            filename = f"complete_audit_{url.replace('https://', '').replace('/', '_')}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"   Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Complete audit failed for {url}: {e}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())