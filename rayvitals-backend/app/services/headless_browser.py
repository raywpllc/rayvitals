"""
Headless browser service for anti-blocking website analysis
"""

import asyncio
import random
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import structlog

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = Exception

logger = structlog.get_logger()


class HeadlessBrowser:
    """Headless browser service for anti-blocking web scraping"""
    
    def __init__(self):
        self.timeout = 30000  # 30 seconds in milliseconds
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        # Realistic browser configurations
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.viewport_sizes = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1280, "height": 720}
        ]
    
    async def fetch_page_content(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch page content using headless browser with anti-blocking measures
        
        Args:
            url: URL to fetch
            options: Additional options (wait_for_load, screenshot, etc.)
            
        Returns:
            Dict containing html, status, headers, metrics, etc.
        """
        if not self.playwright_available:
            raise ImportError("Playwright not available. Install with: pip install playwright")
        
        options = options or {}
        result = {
            "html": None,
            "status": None,
            "headers": {},
            "metrics": {},
            "screenshot": None,
            "error": None,
            "method": "playwright"
        }
        
        try:
            async with async_playwright() as p:
                # Use chromium by default (most stable)
                browser_type = p.chromium
                
                # Launch browser with stealth settings
                browser = await browser_type.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-extensions",
                        "--disable-plugins",
                        "--disable-default-apps",
                        "--disable-background-timer-throttling",
                        "--disable-renderer-backgrounding",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-features=TranslateUI",
                        "--disable-ipc-flooding-protection",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--no-pings",
                        "--password-store=basic",
                        "--use-mock-keychain",
                    ]
                )
                
                # Create context with random user agent and viewport
                user_agent = random.choice(self.user_agents)
                viewport = random.choice(self.viewport_sizes)
                
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport=viewport,
                    java_script_enabled=True,
                    ignore_https_errors=True,
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0"
                    }
                )
                
                # Add stealth measures
                await context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Denoted.denied }) :
                            originalQuery(parameters)
                    );
                """)
                
                page = await context.new_page()
                
                # Set up response listener
                response_data = {}
                
                async def handle_response(response):
                    if response.url == url:
                        response_data['status'] = response.status
                        response_data['headers'] = await response.all_headers()
                
                page.on('response', handle_response)
                
                # Add random delay before navigation
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                # Navigate to page
                start_time = time.time()
                
                try:
                    response = await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.timeout
                    )
                    
                    # Wait for additional loading if specified
                    if options.get("wait_for_load", True):
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Get page content
                    result["html"] = await page.content()
                    result["status"] = response.status if response else response_data.get('status')
                    result["headers"] = response_data.get('headers', {})
                    
                    # Calculate metrics
                    load_time = (time.time() - start_time) * 1000
                    result["metrics"] = {
                        "load_time": load_time,
                        "page_size": len(result["html"]) if result["html"] else 0,
                        "user_agent": user_agent,
                        "viewport": viewport
                    }
                    
                    # Take screenshot if requested
                    if options.get("screenshot", False):
                        result["screenshot"] = await page.screenshot()
                    
                    logger.info("Headless browser fetch successful", 
                               url=url, 
                               status=result["status"],
                               load_time=load_time,
                               page_size=result["metrics"]["page_size"])
                    
                except PlaywrightTimeoutError as e:
                    result["error"] = f"Timeout: {str(e)}"
                    logger.error("Headless browser timeout", error=str(e), url=url)
                    
                except Exception as e:
                    result["error"] = f"Navigation error: {str(e)}"
                    logger.error("Headless browser navigation error", error=str(e), url=url)
                
                finally:
                    await context.close()
                    await browser.close()
                
        except Exception as e:
            result["error"] = f"Browser launch error: {str(e)}"
            logger.error("Headless browser launch error", error=str(e), url=url)
        
        return result
    
    async def get_page_performance_metrics(self, url: str) -> Dict[str, Any]:
        """Get detailed performance metrics using headless browser"""
        if not self.playwright_available:
            raise ImportError("Playwright not available")
        
        metrics = {}
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Start performance monitoring
                await page.goto(url, wait_until="networkidle")
                
                # Get performance metrics
                performance_metrics = await page.evaluate("""
                    () => {
                        const perfData = performance.getEntriesByType('navigation')[0];
                        const paintData = performance.getEntriesByType('paint');
                        
                        return {
                            dns_lookup: perfData.domainLookupEnd - perfData.domainLookupStart,
                            tcp_connect: perfData.connectEnd - perfData.connectStart,
                            request_time: perfData.responseStart - perfData.requestStart,
                            response_time: perfData.responseEnd - perfData.responseStart,
                            dom_loading: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                            page_load: perfData.loadEventEnd - perfData.loadEventStart,
                            first_paint: paintData.find(p => p.name === 'first-paint')?.startTime || 0,
                            first_contentful_paint: paintData.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                            total_load_time: perfData.loadEventEnd - perfData.fetchStart
                        };
                    }
                """)
                
                metrics = performance_metrics
                
                await context.close()
                await browser.close()
                
        except Exception as e:
            logger.error("Performance metrics collection failed", error=str(e), url=url)
            metrics["error"] = str(e)
        
        return metrics
    
    async def check_mobile_responsiveness(self, url: str) -> Dict[str, Any]:
        """Check mobile responsiveness using different viewport sizes"""
        if not self.playwright_available:
            raise ImportError("Playwright not available")
        
        results = {
            "mobile_friendly": False,
            "responsive_design": False,
            "viewport_tests": {}
        }
        
        viewports = [
            {"name": "mobile", "width": 375, "height": 667},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1920, "height": 1080}
        ]
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                for viewport in viewports:
                    context = await browser.new_context(
                        viewport={"width": viewport["width"], "height": viewport["height"]},
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                    )
                    
                    page = await context.new_page()
                    
                    try:
                        await page.goto(url, wait_until="domcontentloaded")
                        
                        # Check for horizontal scrolling
                        scroll_width = await page.evaluate("document.body.scrollWidth")
                        client_width = await page.evaluate("document.body.clientWidth")
                        
                        # Check viewport meta tag
                        viewport_meta = await page.evaluate("""
                            () => {
                                const meta = document.querySelector('meta[name="viewport"]');
                                return meta ? meta.getAttribute('content') : null;
                            }
                        """)
                        
                        results["viewport_tests"][viewport["name"]] = {
                            "has_horizontal_scroll": scroll_width > client_width,
                            "viewport_meta": viewport_meta,
                            "scroll_width": scroll_width,
                            "client_width": client_width
                        }
                        
                        if viewport["name"] == "mobile":
                            results["mobile_friendly"] = viewport_meta is not None and "width=device-width" in viewport_meta
                        
                    except Exception as e:
                        results["viewport_tests"][viewport["name"]] = {"error": str(e)}
                    
                    finally:
                        await context.close()
                
                await browser.close()
                
                # Determine if responsive
                mobile_test = results["viewport_tests"].get("mobile", {})
                tablet_test = results["viewport_tests"].get("tablet", {})
                
                results["responsive_design"] = (
                    not mobile_test.get("has_horizontal_scroll", True) and
                    not tablet_test.get("has_horizontal_scroll", True) and
                    results["mobile_friendly"]
                )
                
        except Exception as e:
            logger.error("Mobile responsiveness check failed", error=str(e), url=url)
            results["error"] = str(e)
        
        return results
    
    def is_available(self) -> bool:
        """Check if headless browser is available"""
        return self.playwright_available