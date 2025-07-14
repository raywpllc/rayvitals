"""
Performance scanning service
"""

import asyncio
import time
from typing import Dict, Any, List
from urllib.parse import urlparse
import httpx
import structlog

logger = structlog.get_logger()


class PerformanceScanner:
    """Performance analysis service"""
    
    def __init__(self):
        self.timeout = 30.0
    
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
                perf_metrics, http_results
            )
            
        except Exception as e:
            logger.error("Performance scan failed", error=str(e), url=url)
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
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # Measure response time
                start_time = time.time()
                response = await client.get(url)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                metrics["response_time"] = round(response_time, 2)
                metrics["page_load_time"] = round(response_time, 2)  # Simple approximation
                metrics["page_size"] = len(response.content)
                metrics["http_status"] = response.status_code
                
                # Count redirects
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
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
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
        if http_status >= 400:
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
    
    def _generate_performance_recommendations(self, perf_metrics: Dict, http_results: Dict) -> tuple:
        """Generate performance issues and recommendations"""
        issues = []
        recommendations = []
        
        # Response time issues
        response_time = perf_metrics.get("response_time", 0)
        if response_time > 3000:
            issues.append(f"Very slow response time: {response_time}ms")
            recommendations.append("Optimize server response time and consider CDN")
        elif response_time > 1000:
            issues.append(f"Slow response time: {response_time}ms")
            recommendations.append("Optimize server performance and database queries")
        
        # Page size issues
        page_size = perf_metrics.get("page_size", 0)
        if page_size > 2 * 1024 * 1024:
            issues.append(f"Large page size: {page_size / (1024*1024):.1f}MB")
            recommendations.append("Optimize images and minify CSS/JS")
        
        # HTTP status issues
        http_status = perf_metrics.get("http_status", 200)
        if http_status >= 400:
            issues.append(f"HTTP error: {http_status}")
            recommendations.append("Fix HTTP errors and broken links")
        
        # Redirect issues
        redirects = perf_metrics.get("redirects", 0)
        if redirects > 1:
            issues.append(f"Multiple redirects: {redirects}")
            recommendations.append("Minimize redirect chains")
        
        # Compression issues
        if not http_results.get("compression_enabled", False):
            issues.append("No compression enabled")
            recommendations.append("Enable gzip/brotli compression")
        
        # Caching issues
        if not http_results.get("cache_headers", {}):
            issues.append("No cache headers")
            recommendations.append("Add cache headers for static resources")
        
        return issues, recommendations