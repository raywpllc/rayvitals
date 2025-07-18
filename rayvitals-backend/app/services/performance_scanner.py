"""
Performance scanning service
"""

import asyncio
import time
from typing import Dict, Any, List
from urllib.parse import urlparse
import httpx
import structlog

from app.services.content_fetcher import ContentFetcher

logger = structlog.get_logger()


class PerformanceScanner:
    """Performance analysis service"""
    
    def __init__(self):
        self.timeout = 30.0
        self.content_fetcher = ContentFetcher()
    
    async def scan_website(self, url: str) -> Dict[str, Any]:
        """Perform comprehensive performance scan"""
        results = {
            "score": 0,
            "issues": [],
            "recommendations": [],
            "metrics": {},
            "page_load_time": None,
            "response_time": None,
            "page_size": None
        }
        
        try:
            # Basic performance metrics
            perf_metrics = await self._measure_performance(url)
            results["metrics"] = perf_metrics
            results["page_load_time"] = perf_metrics.get("page_load_time")
            results["response_time"] = perf_metrics.get("response_time")
            results["page_size"] = perf_metrics.get("page_size")
            
            # HTTP response analysis
            http_results = await self._analyze_http_response(url)
            results["metrics"].update(http_results)
            
            # Calculate performance score
            results["score"] = self._calculate_performance_score(perf_metrics, http_results)
            
            # Generate issues and recommendations
            results["issues"], results["recommendations"] = self._generate_performance_recommendations(
                perf_metrics, http_results, url
            )
            
        except Exception as e:
            logger.error("Performance scan failed", error=str(e), url=url)
            # Provide fallback score for common HTTP errors
            if "403" in str(e):
                results["score"] = 75  # Neutral-positive score - not the website's fault
                results["issues"].append("⚠️ Automated access blocked - this is NOT a website performance issue")
                results["recommendations"].append("Manual performance testing recommended")
                results["recommendations"].append("Use browser dev tools or online performance testing services")
                # Add note that this is a testing limitation, not website fault
                results["note"] = "403 blocking indicates anti-bot protection, not performance problems"
            elif "404" in str(e):
                results["score"] = 0
                results["issues"].append("Page not found - cannot analyze performance")
            elif "timeout" in str(e).lower() or "timed out" in str(e).lower():
                results["score"] = 30  # Low score for timeouts - this IS a performance issue
                results["issues"].append("Request timed out - indicates slow website performance")
                results["recommendations"].append("Optimize server response time and reduce page load time")
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                results["score"] = 70  # Neutral score for network issues
                results["issues"].append("⚠️ Network connection issue - this is NOT a website performance problem")
                results["recommendations"].append("Retry analysis or check network connectivity")
            else:
                results["score"] = 0
                results["issues"].append(f"Performance scan failed: {str(e)}")
        
        return results
    
    async def _measure_performance(self, url: str) -> Dict[str, Any]:
        """Measure basic performance metrics"""
        metrics = {
            "page_load_time": None,
            "response_time": None,
            "page_size": None,
            "http_status": None,
            "redirects": 0
        }
        
        try:
            # Try to get performance metrics from content fetcher (includes headless browser)
            perf_metrics = await self.content_fetcher.get_performance_metrics(url)
            
            if perf_metrics.get("total_load_time"):
                metrics["response_time"] = round(perf_metrics["total_load_time"], 2)
                metrics["page_load_time"] = round(perf_metrics["total_load_time"], 2)
                metrics["page_size"] = perf_metrics.get("page_size", 0)
                metrics["http_status"] = perf_metrics.get("status_code", 200)
                
                # Additional metrics from headless browser if available
                if "method" in perf_metrics and perf_metrics["method"] != "failed":
                    if perf_metrics.get("dns_lookup"):
                        metrics["dns_lookup"] = round(perf_metrics["dns_lookup"], 2)
                    if perf_metrics.get("tcp_connect"):
                        metrics["tcp_connect"] = round(perf_metrics["tcp_connect"], 2)
                    if perf_metrics.get("first_contentful_paint"):
                        metrics["first_contentful_paint"] = round(perf_metrics["first_contentful_paint"], 2)
            else:
                # Fallback to basic HTTP measurement
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with httpx.AsyncClient(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
                    start_time = time.time()
                    response = await client.get(url)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    metrics["response_time"] = round(response_time, 2)
                    metrics["page_load_time"] = round(response_time, 2)
                    metrics["page_size"] = len(response.content)
                    metrics["http_status"] = response.status_code
                    
                    if hasattr(response, 'history'):
                        metrics["redirects"] = len(response.history)
                
        except Exception as e:
            logger.error("Performance measurement failed", error=str(e), url=url)
        
        return metrics
    
    async def _analyze_http_response(self, url: str) -> Dict[str, Any]:
        """Analyze HTTP response for performance insights"""
        results = {
            "compression_enabled": False,
            "keep_alive_enabled": False,
            "cache_headers": {},
            "content_type": None,
            "server_response_time": None
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url)
                
                # Check compression
                if "content-encoding" in response.headers:
                    encoding = response.headers["content-encoding"]
                    if encoding in ["gzip", "deflate", "br"]:
                        results["compression_enabled"] = True
                
                # Check keep-alive
                if "connection" in response.headers:
                    if "keep-alive" in response.headers["connection"].lower():
                        results["keep_alive_enabled"] = True
                
                # Cache headers
                cache_headers = {}
                for header in ["cache-control", "expires", "last-modified", "etag"]:
                    if header in response.headers:
                        cache_headers[header] = response.headers[header]
                results["cache_headers"] = cache_headers
                
                # Content type
                results["content_type"] = response.headers.get("content-type", "")
                
                # Server response time (from server header if available)
                if "server-timing" in response.headers:
                    results["server_response_time"] = response.headers["server-timing"]
                
        except Exception as e:
            logger.error("HTTP response analysis failed", error=str(e), url=url)
        
        return results
    
    def _calculate_performance_score(self, perf_metrics: Dict, http_results: Dict) -> float:
        """Calculate overall performance score"""
        score = 100
        
        # Response time scoring
        response_time = perf_metrics.get("response_time", 0)
        if response_time > 3000:  # > 3 seconds
            score -= 40
        elif response_time > 2000:  # > 2 seconds
            score -= 30
        elif response_time > 1000:  # > 1 second
            score -= 20
        elif response_time > 500:  # > 0.5 seconds
            score -= 10
        
        # Page size scoring
        page_size = perf_metrics.get("page_size", 0)
        if page_size > 5 * 1024 * 1024:  # > 5MB
            score -= 25
        elif page_size > 2 * 1024 * 1024:  # > 2MB
            score -= 15
        elif page_size > 1024 * 1024:  # > 1MB
            score -= 10
        
        # HTTP status
        http_status = perf_metrics.get("http_status", 200)
        if http_status == 403:
            # 403 is typically bot blocking, not a performance issue - minimal penalty
            score -= 5
        elif http_status >= 400:
            score -= 30
        elif http_status >= 300:
            score -= 10
        
        # Redirects
        redirects = perf_metrics.get("redirects", 0)
        if redirects > 3:
            score -= 20
        elif redirects > 1:
            score -= 10
        
        # Compression
        if not http_results.get("compression_enabled", False):
            score -= 15
        
        # Caching
        if not http_results.get("cache_headers", {}):
            score -= 10
        
        return max(0, min(100, round(score, 1)))
    
    def _get_performance_location(self, url: str, issue_type: str, details: str = "") -> Dict[str, Any]:
        """Get location information for performance issues"""
        location = {
            "url": url,
            "selector": "",
            "html_snippet": "",
            "line_number": None
        }
        
        if issue_type == "response_time":
            location["selector"] = "Server response"
            location["html_snippet"] = f"Server response time: {details}"
        elif issue_type == "page_size":
            location["selector"] = "Page resources"
            location["html_snippet"] = f"Page size: {details}"
        elif issue_type == "http_status":
            location["selector"] = "HTTP response"
            location["html_snippet"] = f"HTTP status: {details}"
        elif issue_type == "redirects":
            location["selector"] = "Redirect chain"
            location["html_snippet"] = f"Redirect count: {details}"
        elif issue_type == "compression":
            location["selector"] = "HTTP headers"
            location["html_snippet"] = "No compression enabled in HTTP headers"
        elif issue_type == "cache_headers":
            location["selector"] = "HTTP headers"
            location["html_snippet"] = "No cache headers in HTTP response"
        else:
            location["selector"] = "general"
            location["html_snippet"] = f"Performance issue: {details}"
        
        return location
    
    def _generate_performance_recommendations(self, perf_metrics: Dict, http_results: Dict, url: str) -> tuple:
        """Generate performance issues and recommendations"""
        issues = []
        recommendations = []
        
        # Response time issues
        response_time = perf_metrics.get("response_time", 0)
        if response_time > 3000:
            issues.append({
                "description": f"Very slow response time: {response_time}ms",
                "location": self._get_performance_location(url, "response_time", f"{response_time}ms"),
                "severity": "high",
                "help": "Optimize server response time and consider CDN"
            })
            recommendations.append("Optimize server response time and consider CDN")
        elif response_time > 1000:
            issues.append({
                "description": f"Slow response time: {response_time}ms",
                "location": self._get_performance_location(url, "response_time", f"{response_time}ms"),
                "severity": "medium",
                "help": "Optimize server performance and database queries"
            })
            recommendations.append("Optimize server performance and database queries")
        
        # Page size issues
        page_size = perf_metrics.get("page_size", 0)
        if page_size > 2 * 1024 * 1024:
            issues.append({
                "description": f"Large page size: {page_size / (1024*1024):.1f}MB",
                "location": self._get_performance_location(url, "page_size", f"{page_size / (1024*1024):.1f}MB"),
                "severity": "medium",
                "help": "Optimize images and minify CSS/JS"
            })
            recommendations.append("Optimize images and minify CSS/JS")
        
        # HTTP status issues
        http_status = perf_metrics.get("http_status", 200)
        if http_status == 403:
            # 403 is typically bot blocking, not a site issue
            issues.append({
                "description": "⚠️ Automated access blocked (403) - this is NOT a website performance issue",
                "location": self._get_performance_location(url, "http_status", "403 (Bot blocked)"),
                "severity": "low",
                "help": "Use manual testing or browser dev tools for performance analysis"
            })
            recommendations.append("Manual performance testing recommended")
        elif http_status >= 400:
            issues.append({
                "description": f"HTTP error: {http_status}",
                "location": self._get_performance_location(url, "http_status", str(http_status)),
                "severity": "high",
                "help": "Fix HTTP errors and broken links"
            })
            recommendations.append("Fix HTTP errors and broken links")
        
        # Redirect issues
        redirects = perf_metrics.get("redirects", 0)
        if redirects > 1:
            issues.append({
                "description": f"Multiple redirects: {redirects}",
                "location": self._get_performance_location(url, "redirects", str(redirects)),
                "severity": "medium",
                "help": "Minimize redirect chains"
            })
            recommendations.append("Minimize redirect chains")
        
        # Compression issues
        if not http_results.get("compression_enabled", False):
            issues.append({
                "description": "No compression enabled",
                "location": self._get_performance_location(url, "compression", "No compression"),
                "severity": "medium",
                "help": "Enable gzip/brotli compression"
            })
            recommendations.append("Enable gzip/brotli compression")
        
        # Caching issues
        if not http_results.get("cache_headers", {}):
            issues.append({
                "description": "No cache headers",
                "location": self._get_performance_location(url, "cache_headers", "No cache headers"),
                "severity": "low",
                "help": "Add cache headers for static resources"
            })
            recommendations.append("Add cache headers for static resources")
        
        return issues, recommendations