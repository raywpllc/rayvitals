"""
Hybrid content fetcher that tries headless browser first, then falls back to HTTP
"""

import asyncio
import time
import random
from typing import Dict, Any, Optional
import httpx
import structlog

from app.services.headless_browser import HeadlessBrowser

logger = structlog.get_logger()


class ContentFetcher:
    """Hybrid content fetcher with multiple strategies"""
    
    def __init__(self):
        self.headless_browser = HeadlessBrowser()
        self.timeout = 30.0
        
        # Request rotation and delays
        self.request_count = 0
        self.last_request_time = 0.0
        self.min_delay = 1.0  # Minimum delay between requests
        self.max_delay = 3.0  # Maximum delay between requests
        
        # Multiple user agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # HTTP fallback headers template
        self.http_headers_template = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def _apply_request_delays(self):
        """Apply request delays for rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay based on request count and time since last request
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # Add extra delay for rapid requests
        if time_since_last < self.min_delay:
            delay += random.uniform(0.5, 1.5)
        
        # Progressive delay for high request count
        if self.request_count > 5:
            delay += random.uniform(1.0, 2.0)
        
        logger.info(f"Applying request delay: {delay:.2f}s", request_count=self.request_count)
        await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
        self.request_count += 1

    def _get_rotated_user_agent(self) -> str:
        """Get a rotated user agent based on request count"""
        return self.user_agents[self.request_count % len(self.user_agents)]

    async def fetch_page_content(self, url: str, prefer_headless: bool = True) -> Dict[str, Any]:
        """
        Fetch page content using the best available method
        
        Args:
            url: URL to fetch
            prefer_headless: Whether to try headless browser first
            
        Returns:
            Dict containing html, status, method used, metrics, etc.
        """
        # Apply request delays for rate limiting
        await self._apply_request_delays()
        
        result = {
            "html": None,
            "status": None,
            "headers": {},
            "metrics": {},
            "method": None,
            "error": None,
            "fallback_used": False
        }
        
        # Strategy 1: Try headless browser first (if available and preferred)
        if prefer_headless and self.headless_browser.is_available():
            logger.info("Attempting headless browser fetch", url=url)
            
            try:
                browser_result = await self.headless_browser.fetch_page_content(url)
                
                if browser_result["html"] and not browser_result["error"]:
                    result.update(browser_result)
                    result["method"] = "headless_browser"
                    logger.info("Headless browser fetch successful", url=url, status=result["status"])
                    return result
                else:
                    logger.warning("Headless browser fetch failed, trying HTTP fallback", 
                                 url=url, error=browser_result.get("error"))
                    
            except Exception as e:
                logger.warning("Headless browser unavailable, trying HTTP fallback", 
                             url=url, error=str(e))
        
        # Strategy 2: HTTP fallback
        logger.info("Attempting HTTP fetch", url=url)
        result["fallback_used"] = True
        
        try:
            http_result = await self._fetch_with_http(url)
            result.update(http_result)
            result["method"] = "http"
            logger.info("HTTP fetch successful", url=url, status=result["status"])
            
        except Exception as e:
            result["error"] = f"All fetch methods failed. Last error: {str(e)}"
            result["method"] = "failed"
            logger.error("All fetch methods failed", url=url, error=str(e))
        
        return result
    
    async def _fetch_with_http(self, url: str) -> Dict[str, Any]:
        """Fetch content using HTTP client with user agent rotation"""
        result = {
            "html": None,
            "status": None,
            "headers": {},
            "metrics": {},
            "error": None
        }
        
        # Get rotated user agent
        user_agent = self._get_rotated_user_agent()
        
        # Build headers with rotated user agent
        headers = {**self.http_headers_template, "User-Agent": user_agent}
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                headers=headers, 
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                
                result["html"] = response.text
                result["status"] = response.status_code
                result["headers"] = dict(response.headers)
                
                load_time = (time.time() - start_time) * 1000
                result["metrics"] = {
                    "load_time": load_time,
                    "page_size": len(response.content),
                    "user_agent": user_agent,
                    "request_count": self.request_count
                }
                
                if response.status_code != 200:
                    result["error"] = f"HTTP {response.status_code} error"
                
        except Exception as e:
            result["error"] = str(e)
            raise
        
        return result
    
    async def get_performance_metrics(self, url: str) -> Dict[str, Any]:
        """Get performance metrics using the best available method"""
        # Try headless browser performance metrics first
        if self.headless_browser.is_available():
            try:
                return await self.headless_browser.get_page_performance_metrics(url)
            except Exception as e:
                logger.warning("Headless performance metrics failed, using HTTP timing", 
                             url=url, error=str(e))
        
        # Fallback to basic HTTP timing
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.http_headers) as client:
                response = await client.get(url)
                load_time = (time.time() - start_time) * 1000
                
                return {
                    "total_load_time": load_time,
                    "page_size": len(response.content),
                    "status_code": response.status_code,
                    "method": "http_timing"
                }
        except Exception as e:
            return {"error": str(e), "method": "failed"}
    
    async def check_mobile_responsiveness(self, url: str) -> Dict[str, Any]:
        """Check mobile responsiveness using headless browser if available"""
        if self.headless_browser.is_available():
            try:
                return await self.headless_browser.check_mobile_responsiveness(url)
            except Exception as e:
                logger.warning("Headless mobile check failed", url=url, error=str(e))
        
        # Fallback: Basic mobile check using HTTP + HTML analysis
        try:
            content_result = await self.fetch_page_content(url, prefer_headless=False)
            
            if content_result["html"]:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content_result["html"], 'html.parser')
                
                # Check for viewport meta tag
                viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
                
                return {
                    "mobile_friendly": viewport_meta is not None and 'width=device-width' in (viewport_meta.get('content') or ''),
                    "responsive_design": False,  # Cannot determine without browser
                    "viewport_meta": viewport_meta.get('content') if viewport_meta else None,
                    "method": "html_analysis"
                }
            else:
                return {"error": "Could not fetch HTML content", "method": "failed"}
                
        except Exception as e:
            return {"error": str(e), "method": "failed"}
    
    def is_headless_available(self) -> bool:
        """Check if headless browser is available"""
        return self.headless_browser.is_available()
    
    async def get_fetch_strategy_info(self) -> Dict[str, Any]:
        """Get information about available fetch strategies"""
        return {
            "headless_browser_available": self.headless_browser.is_available(),
            "http_fallback_available": True,
            "recommended_strategy": "headless_browser" if self.headless_browser.is_available() else "http",
            "anti_blocking_features": {
                "user_agent_rotation": True,  # Available in both headless and HTTP
                "viewport_randomization": self.headless_browser.is_available(),
                "javascript_execution": self.headless_browser.is_available(),
                "stealth_mode": self.headless_browser.is_available(),
                "request_delays": True,  # Available in both modes
                "progressive_delays": True,  # Available in both modes
                "rate_limiting": True  # Available in both modes
            },
            "rate_limiting": {
                "min_delay": self.min_delay,
                "max_delay": self.max_delay,
                "request_count": self.request_count
            }
        }