#!/usr/bin/env python3
"""
Local test interface for RayVitals scanners without database
"""

import asyncio
import json
import time
from typing import Dict, Any
from app.services.security_scanner import SecurityScanner
from app.services.performance_scanner import PerformanceScanner
from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner


class LocalAuditService:
    """Local audit service for testing without database"""
    
    def __init__(self):
        self.security_scanner = SecurityScanner()
        self.performance_scanner = PerformanceScanner()
        self.accessibility_scanner = AccessibilityScanner()
        self.ux_scanner = UXScanner()
    
    async def run_audit(self, url: str) -> Dict[str, Any]:
        """Run complete audit locally"""
        start_time = time.time()
        
        print(f"\n🔍 Starting audit for: {url}")
        print("=" * 60)
        
        audit_results = {}
        
        try:
            # Security analysis
            print("\n🔒 Running security analysis...")
            security_results = await self.security_scanner.scan_website(url)
            audit_results["security"] = security_results
            print(f"   Security score: {security_results.get('score', 0)}")
            
            # Performance analysis
            print("\n⚡ Running performance analysis...")
            performance_results = await self.performance_scanner.scan_website(url)
            audit_results["performance"] = performance_results
            print(f"   Performance score: {performance_results.get('score', 0)}")
            
            # UX analysis
            print("\n👥 Running UX analysis...")
            ux_results = await self.ux_scanner.scan_website(url)
            audit_results["ux"] = ux_results
            print(f"   UX score: {ux_results.get('score', 0)}")
            
            # Accessibility analysis
            print("\n♿ Running accessibility analysis...")
            accessibility_results = await self.accessibility_scanner.scan_website(url)
            audit_results["accessibility"] = accessibility_results
            print(f"   Accessibility score: {accessibility_results.get('score', 0)}")
            
            # Calculate scores
            scores = self._calculate_scores(audit_results)
            
            processing_time = time.time() - start_time
            
            # Display results
            print(f"\n🎯 AUDIT RESULTS")
            print("=" * 60)
            print(f"Overall Score: {scores['overall']}")
            print(f"Security: {scores['security']}")
            print(f"Performance: {scores['performance']}")
            print(f"UX: {scores['ux']}")
            print(f"Accessibility: {scores['accessibility']}")
            print(f"Processing time: {processing_time:.2f}s")
            
            # Show key issues
            self._display_key_issues(audit_results)
            
            return {
                "scores": scores,
                "results": audit_results,
                "processing_time": processing_time
            }
            
        except Exception as e:
            print(f"❌ Audit failed: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_scores(self, audit_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate category and overall scores"""
        scores = {
            "security": audit_results.get("security", {}).get("score", 0),
            "performance": audit_results.get("performance", {}).get("score", 0),
            "seo": 75,  # Placeholder for now
            "ux": audit_results.get("ux", {}).get("score", 0),
            "accessibility": audit_results.get("accessibility", {}).get("score", 0),
        }
        
        # Calculate overall score with weights from spec
        weights = {
            "security": 0.25,
            "performance": 0.25,
            "seo": 0.20,
            "ux": 0.20,
            "accessibility": 0.10
        }
        
        overall_score = sum(scores[category] * weights[category] for category in scores)
        scores["overall"] = round(overall_score, 1)
        
        return scores
    
    def _display_key_issues(self, audit_results: Dict[str, Any]):
        """Display key issues found"""
        print(f"\n🚨 KEY ISSUES FOUND")
        print("=" * 60)
        
        for category, results in audit_results.items():
            issues = results.get("issues", [])
            if issues:
                print(f"\n{category.upper()}:")
                for issue in issues[:3]:  # Show top 3 issues
                    print(f"  • {issue}")
                if len(issues) > 3:
                    print(f"  ... and {len(issues) - 3} more")


async def main():
    """Main test function"""
    print("🎯 RayVitals Local Scanner Test")
    print("=" * 60)
    
    # Test with different URLs
    test_urls = [
        "https://example.com",
        "https://google.com",
        "https://github.com"
    ]
    
    # Get URL from user input
    url = input("\nEnter URL to test (or press Enter for example.com): ").strip()
    if not url:
        url = "https://example.com"
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    audit_service = LocalAuditService()
    results = await audit_service.run_audit(url)
    
    # Option to save results to file
    save_results = input("\nSave detailed results to file? (y/n): ").strip().lower()
    if save_results == 'y':
        filename = f"audit_results_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())