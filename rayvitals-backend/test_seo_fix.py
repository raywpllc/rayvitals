#!/usr/bin/env python3
"""Test SEO scanner fix"""

import asyncio
from app.services.audit_service import AuditService

async def test_seo():
    audit_service = AuditService()
    url = "https://tailfin.com"
    
    print(f"Testing SEO analysis for {url}...")
    result = await audit_service._basic_seo_analysis(url)
    
    print(f"\nSEO Score: {result['score']}")
    print(f"Issues: {result['issues']}")
    print(f"Recommendations: {result['recommendations']}")

if __name__ == "__main__":
    asyncio.run(test_seo())