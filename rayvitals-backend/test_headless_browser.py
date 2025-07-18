#!/usr/bin/env python3
"""
Test script for headless browser integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.content_fetcher import ContentFetcher
from app.services.headless_browser import HeadlessBrowser


async def test_headless_browser():
    """Test headless browser functionality"""
    
    print("🚀 Testing Headless Browser Integration")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://httpbin.org/get",
        "https://github.com"
    ]
    
    # Initialize services
    content_fetcher = ContentFetcher()
    headless_browser = HeadlessBrowser()
    
    # Check if headless browser is available
    print(f"Headless browser available: {headless_browser.is_available()}")
    
    # Test strategy info
    strategy_info = await content_fetcher.get_fetch_strategy_info()
    print(f"Strategy info: {strategy_info}")
    
    print("\n" + "=" * 50)
    
    for url in test_urls:
        print(f"\n📋 Testing URL: {url}")
        print("-" * 30)
        
        try:
            # Test content fetching
            result = await content_fetcher.fetch_page_content(url)
            
            print(f"✅ Method used: {result.get('method', 'unknown')}")
            print(f"✅ Status: {result.get('status', 'unknown')}")
            print(f"✅ Content length: {len(result.get('html', ''))}")
            print(f"✅ Fallback used: {result.get('fallback_used', False)}")
            
            if result.get('error'):
                print(f"⚠️  Error: {result['error']}")
            
            # Test performance metrics
            print("\n📊 Performance Metrics:")
            perf_metrics = await content_fetcher.get_performance_metrics(url)
            
            if perf_metrics.get('total_load_time'):
                print(f"✅ Load time: {perf_metrics['total_load_time']:.2f}ms")
            if perf_metrics.get('page_size'):
                print(f"✅ Page size: {perf_metrics['page_size']} bytes")
            if perf_metrics.get('method'):
                print(f"✅ Method: {perf_metrics['method']}")
                
            if perf_metrics.get('error'):
                print(f"⚠️  Performance error: {perf_metrics['error']}")
            
            # Test mobile responsiveness
            print("\n📱 Mobile Responsiveness:")
            mobile_check = await content_fetcher.check_mobile_responsiveness(url)
            
            if mobile_check.get('mobile_friendly') is not None:
                print(f"✅ Mobile friendly: {mobile_check['mobile_friendly']}")
            if mobile_check.get('responsive_design') is not None:
                print(f"✅ Responsive design: {mobile_check['responsive_design']}")
            if mobile_check.get('viewport_meta'):
                print(f"✅ Viewport meta: {mobile_check['viewport_meta']}")
            if mobile_check.get('method'):
                print(f"✅ Method: {mobile_check['method']}")
                
            if mobile_check.get('error'):
                print(f"⚠️  Mobile error: {mobile_check['error']}")
            
        except Exception as e:
            print(f"❌ Error testing {url}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing Complete")


if __name__ == "__main__":
    asyncio.run(test_headless_browser())