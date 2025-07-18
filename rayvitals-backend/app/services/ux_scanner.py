"""
UX (User Experience) scanning service for mobile-first analysis
"""

import asyncio
import json
import re
from typing import Dict, Any, List
from urllib.parse import urlparse, urljoin
import httpx
import structlog
from bs4 import BeautifulSoup

from app.services.content_fetcher import ContentFetcher

logger = structlog.get_logger()


class UXScanner:
    """User Experience analysis service"""
    
    def __init__(self):
        self.timeout = 30.0
        self.content_fetcher = ContentFetcher()
    
    async def scan_website(self, url: str) -> Dict[str, Any]:
        """Perform comprehensive UX scan"""
        results = {
            "score": 0,
            "issues": [],
            "recommendations": [],
            "mobile_responsiveness": {},
            "touch_targets": {},
            "navigation": {},
            "readability": {},
            "layout_stability": {},
            "form_usability": {}
        }
        
        try:
            # Get page content
            page_content = await self._fetch_page_content(url)
            
            # Mobile responsiveness analysis
            mobile_results = await self._analyze_mobile_responsiveness(page_content)
            results["mobile_responsiveness"] = mobile_results
            
            # Touch target analysis
            touch_results = await self._analyze_touch_targets(page_content)
            results["touch_targets"] = touch_results
            
            # Navigation analysis
            nav_results = await self._analyze_navigation(page_content)
            results["navigation"] = nav_results
            
            # Content readability analysis
            readability_results = await self._analyze_readability(page_content)
            results["readability"] = readability_results
            
            # Layout stability analysis
            layout_results = await self._analyze_layout_stability(page_content)
            results["layout_stability"] = layout_results
            
            # Form usability analysis
            form_results = await self._analyze_form_usability(page_content)
            results["form_usability"] = form_results
            
            # Calculate overall UX score
            results["score"] = self._calculate_ux_score(
                mobile_results, touch_results, nav_results, 
                readability_results, layout_results, form_results
            )
            
            # Generate issues and recommendations
            results["issues"], results["recommendations"] = self._generate_ux_recommendations(
                mobile_results, touch_results, nav_results, 
                readability_results, layout_results, form_results, url
            )
            
        except Exception as e:
            logger.error("UX scan failed", error=str(e), url=url)
            # Provide fallback score for common HTTP errors
            if "403" in str(e):
                results["score"] = 75  # Neutral-positive score - not the website's fault
                results["issues"].append("⚠️ Automated access blocked - this is NOT a website UX issue")
                results["recommendations"].append("Manual UX testing recommended")
                results["recommendations"].append("Test with real users across different devices")
                # Add note that this is a testing limitation, not website fault
                results["note"] = "403 blocking indicates anti-bot protection, not UX problems"
            elif "404" in str(e):
                results["score"] = 0
                results["issues"].append("Page not found - cannot analyze UX")
            elif "timeout" in str(e).lower() or "timed out" in str(e).lower():
                results["score"] = 60  # Neutral score for timeouts
                results["issues"].append("⚠️ Request timed out - this may indicate slow loading affecting UX")
                results["recommendations"].append("Check website loading speed and optimize performance")
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                results["score"] = 70  # Neutral score for network issues
                results["issues"].append("⚠️ Network connection issue - this is NOT a website UX problem")
                results["recommendations"].append("Retry analysis or check network connectivity")
            else:
                results["score"] = 0
                results["issues"].append(f"UX scan failed: {str(e)}")
        
        return results
    
    async def _fetch_page_content(self, url: str) -> str:
        """Fetch page HTML content using content fetcher"""
        try:
            content_result = await self.content_fetcher.fetch_page_content(url)
            
            if content_result.get("html"):
                return content_result["html"]
            elif content_result.get("error"):
                raise Exception(content_result["error"])
            else:
                raise Exception("No content received")
        except Exception as e:
            logger.error("Failed to fetch page content", error=str(e), url=url)
            raise
    
    async def _analyze_mobile_responsiveness(self, html_content: str) -> Dict[str, Any]:
        """Analyze mobile responsiveness"""
        results = {
            "score": 85,
            "issues": [],
            "viewport_configured": False,
            "responsive_images": 0,
            "fixed_width_elements": 0,
            "mobile_friendly_fonts": True
        }
        
        # Try to get mobile responsiveness check from content fetcher first
        try:
            mobile_check = await self.content_fetcher.check_mobile_responsiveness("dummy_url")
            if mobile_check.get("mobile_friendly"):
                results["viewport_configured"] = True
                results["score"] = 95  # Higher score for headless browser verification
            elif mobile_check.get("viewport_meta"):
                results["viewport_configured"] = True
                content = mobile_check.get("viewport_meta", "")
                if 'width=device-width' not in content:
                    results["issues"].append("Viewport meta tag should include width=device-width")
        except Exception:
            pass  # Fall back to HTML analysis
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for viewport meta tag (fallback or additional check)
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            results["viewport_configured"] = True
            content = viewport_meta.get('content', '')
            if 'width=device-width' not in content:
                results["issues"].append("Viewport meta tag should include width=device-width")
        else:
            results["issues"].append("Missing viewport meta tag")
            results["score"] -= 20
        
        # Check for responsive images
        images = soup.find_all('img')
        responsive_images = 0
        
        for img in images:
            # Check for srcset or picture element
            if img.get('srcset') or img.parent.name == 'picture':
                responsive_images += 1
        
        results["responsive_images"] = responsive_images
        if len(images) > 0:
            responsive_ratio = responsive_images / len(images)
            if responsive_ratio < 0.5:
                results["issues"].append("Few images are responsive")
                results["score"] -= 10
        
        # Check for fixed width elements (simplified)
        style_tags = soup.find_all('style')
        inline_styles = soup.find_all(attrs={'style': True})
        
        fixed_width_count = 0
        for element in inline_styles:
            style = element.get('style', '')
            if 'width:' in style and 'px' in style:
                fixed_width_count += 1
        
        results["fixed_width_elements"] = fixed_width_count
        if fixed_width_count > 5:
            results["issues"].append("Many elements have fixed pixel widths")
            results["score"] -= 15
        
        return results
    
    async def _analyze_touch_targets(self, html_content: str) -> Dict[str, Any]:
        """Analyze touch target sizes and spacing"""
        results = {
            "score": 80,
            "issues": [],
            "interactive_elements": 0,
            "potential_small_targets": 0,
            "close_elements": 0
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find interactive elements
        interactive_selectors = ['button', 'a', 'input[type="submit"]', 'input[type="button"]']
        interactive_elements = []
        
        for selector in interactive_selectors:
            if selector.startswith('input'):
                elements = soup.find_all('input', {'type': selector.split('[')[1].split('=')[1].strip('"')})
            else:
                elements = soup.find_all(selector)
            interactive_elements.extend(elements)
        
        results["interactive_elements"] = len(interactive_elements)
        
        # Check for potentially small touch targets
        small_targets = 0
        for element in interactive_elements:
            # Check for inline styles that might indicate small size
            style = element.get('style', '')
            if 'font-size' in style:
                # Extract font-size value
                font_size_match = re.search(r'font-size:\s*(\d+)px', style)
                if font_size_match:
                    font_size = int(font_size_match.group(1))
                    if font_size < 14:  # Considered small for touch
                        small_targets += 1
        
        results["potential_small_targets"] = small_targets
        if small_targets > 0:
            results["issues"].append(f"Found {small_targets} potentially small touch targets")
            results["score"] -= min(30, small_targets * 5)
        
        # Check for elements that might be too close together
        # This is a simplified check - real implementation would analyze positioning
        if len(interactive_elements) > 10:
            results["close_elements"] = len(interactive_elements) // 5  # Estimate
            results["issues"].append("Many interactive elements may be too close together")
            results["score"] -= 10
        
        return results
    
    async def _analyze_navigation(self, html_content: str) -> Dict[str, Any]:
        """Analyze navigation structure and clarity"""
        results = {
            "score": 75,
            "issues": [],
            "main_navigation": False,
            "breadcrumbs": False,
            "search_functionality": False,
            "navigation_depth": 0,
            "mobile_navigation": False
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for main navigation
        nav_elements = soup.find_all('nav')
        if nav_elements:
            results["main_navigation"] = True
            
            # Analyze navigation depth
            for nav in nav_elements:
                links = nav.find_all('a')
                if links:
                    results["navigation_depth"] = max(results["navigation_depth"], len(links))
        else:
            results["issues"].append("No main navigation found")
            results["score"] -= 20
        
        # Check for breadcrumbs
        breadcrumb_indicators = soup.find_all(class_=re.compile(r'breadcrumb', re.I))
        if breadcrumb_indicators:
            results["breadcrumbs"] = True
        
        # Check for search functionality
        search_inputs = soup.find_all('input', {'type': 'search'}) + \
                       soup.find_all('input', {'name': re.compile(r'search', re.I)})
        if search_inputs:
            results["search_functionality"] = True
        
        # Check for mobile navigation patterns
        mobile_nav_indicators = soup.find_all(class_=re.compile(r'hamburger|menu-toggle|mobile-menu', re.I))
        if mobile_nav_indicators:
            results["mobile_navigation"] = True
        else:
            results["issues"].append("No mobile navigation pattern detected")
            results["score"] -= 15
        
        # Navigation depth scoring
        if results["navigation_depth"] > 20:
            results["issues"].append("Navigation menu may be too complex")
            results["score"] -= 10
        
        return results
    
    async def _analyze_readability(self, html_content: str) -> Dict[str, Any]:
        """Analyze content readability"""
        results = {
            "score": 80,
            "issues": [],
            "text_content": "",
            "word_count": 0,
            "paragraph_count": 0,
            "heading_distribution": {},
            "font_size_issues": 0,
            "text_color_contrast": True
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text content
        text_elements = soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        all_text = ' '.join([elem.get_text().strip() for elem in text_elements if elem.get_text().strip()])
        
        results["text_content"] = all_text[:500]  # First 500 chars for analysis
        results["word_count"] = len(all_text.split())
        
        # Count paragraphs
        paragraphs = soup.find_all('p')
        results["paragraph_count"] = len(paragraphs)
        
        # Analyze heading distribution
        heading_counts = {}
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            if headings:
                heading_counts[f'h{level}'] = len(headings)
        
        results["heading_distribution"] = heading_counts
        
        # Check for readability issues
        if results["word_count"] < 100:
            results["issues"].append("Very little text content")
            results["score"] -= 15
        
        if results["paragraph_count"] == 0:
            results["issues"].append("No paragraphs found")
            results["score"] -= 10
        
        # Check for very long paragraphs
        long_paragraphs = 0
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text.split()) > 100:  # More than 100 words
                long_paragraphs += 1
        
        if long_paragraphs > 0:
            results["issues"].append(f"Found {long_paragraphs} very long paragraphs")
            results["score"] -= min(20, long_paragraphs * 5)
        
        # Check heading hierarchy
        if 'h1' not in heading_counts:
            results["issues"].append("No H1 heading found")
            results["score"] -= 10
        
        return results
    
    async def _analyze_layout_stability(self, html_content: str) -> Dict[str, Any]:
        """Analyze layout stability factors"""
        results = {
            "score": 85,
            "issues": [],
            "images_without_dimensions": 0,
            "dynamic_content_indicators": 0,
            "loading_indicators": False,
            "font_loading_optimization": False
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for images without dimensions
        images = soup.find_all('img')
        images_without_dims = 0
        
        for img in images:
            if not img.get('width') and not img.get('height'):
                # Check for CSS dimensions in style attribute
                style = img.get('style', '')
                if 'width:' not in style and 'height:' not in style:
                    images_without_dims += 1
        
        results["images_without_dimensions"] = images_without_dims
        if images_without_dims > 0:
            results["issues"].append(f"{images_without_dims} images without dimensions")
            results["score"] -= min(25, images_without_dims * 5)
        
        # Check for dynamic content indicators
        dynamic_indicators = soup.find_all(class_=re.compile(r'lazy|loader|placeholder', re.I))
        results["dynamic_content_indicators"] = len(dynamic_indicators)
        
        # Check for loading indicators
        loading_elements = soup.find_all(class_=re.compile(r'loading|spinner', re.I))
        if loading_elements:
            results["loading_indicators"] = True
        
        # Check for font loading optimization
        link_elements = soup.find_all('link', {'rel': 'preload'})
        for link in link_elements:
            if link.get('as') == 'font':
                results["font_loading_optimization"] = True
                break
        
        return results
    
    async def _analyze_form_usability(self, html_content: str) -> Dict[str, Any]:
        """Analyze form usability"""
        results = {
            "score": 90,
            "issues": [],
            "forms_found": 0,
            "inputs_with_labels": 0,
            "inputs_without_labels": 0,
            "required_field_indicators": 0,
            "error_handling": False
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find forms
        forms = soup.find_all('form')
        results["forms_found"] = len(forms)
        
        if len(forms) == 0:
            return results  # No forms to analyze
        
        # Analyze form inputs
        all_inputs = soup.find_all('input', {'type': lambda x: x not in ['submit', 'button', 'hidden']})
        all_inputs.extend(soup.find_all(['textarea', 'select']))
        
        inputs_with_labels = 0
        inputs_without_labels = 0
        
        for input_elem in all_inputs:
            input_id = input_elem.get('id')
            has_label = False
            
            # Check for associated label
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            # Check for aria-label or aria-labelledby
            if not has_label:
                if input_elem.get('aria-label') or input_elem.get('aria-labelledby'):
                    has_label = True
            
            if has_label:
                inputs_with_labels += 1
            else:
                inputs_without_labels += 1
        
        results["inputs_with_labels"] = inputs_with_labels
        results["inputs_without_labels"] = inputs_without_labels
        
        if inputs_without_labels > 0:
            results["issues"].append(f"{inputs_without_labels} form inputs without labels")
            results["score"] -= min(30, inputs_without_labels * 10)
        
        # Check for required field indicators
        required_inputs = soup.find_all(attrs={'required': True})
        asterisk_indicators = soup.find_all(text=re.compile(r'\*'))
        
        results["required_field_indicators"] = len(required_inputs) + len(asterisk_indicators)
        
        # Check for error handling elements
        error_elements = soup.find_all(class_=re.compile(r'error|invalid|warning', re.I))
        if error_elements:
            results["error_handling"] = True
        
        return results
    
    def _calculate_ux_score(self, mobile_results: Dict, touch_results: Dict, nav_results: Dict,
                           readability_results: Dict, layout_results: Dict, form_results: Dict) -> float:
        """Calculate overall UX score"""
        
        # Get individual scores
        mobile_score = mobile_results.get("score", 85)
        touch_score = touch_results.get("score", 80)
        nav_score = nav_results.get("score", 75)
        readability_score = readability_results.get("score", 80)
        layout_score = layout_results.get("score", 85)
        form_score = form_results.get("score", 90)
        
        # Weighted average - mobile-first approach
        weights = {
            "mobile": 0.25,     # Mobile responsiveness is crucial
            "touch": 0.20,      # Touch targets are important for mobile
            "navigation": 0.20,  # Navigation affects user flow
            "readability": 0.15, # Content readability
            "layout": 0.15,     # Layout stability
            "forms": 0.05       # Form usability (if no forms, this doesn't hurt score)
        }
        
        # If no forms found, redistribute form weight to other categories
        if form_results.get("forms_found", 0) == 0:
            weights["mobile"] += 0.02
            weights["touch"] += 0.01
            weights["navigation"] += 0.01
            weights["readability"] += 0.01
            weights["forms"] = 0
        
        overall_score = (
            mobile_score * weights["mobile"] +
            touch_score * weights["touch"] +
            nav_score * weights["navigation"] +
            readability_score * weights["readability"] +
            layout_score * weights["layout"] +
            form_score * weights["forms"]
        )
        
        return max(0, min(100, round(overall_score, 1)))
    
    def _get_ux_location(self, url: str, issue_type: str, details: str = "") -> Dict[str, Any]:
        """Get location information for UX issues"""
        location = {
            "url": url,
            "selector": "",
            "html_snippet": "",
            "line_number": None
        }
        
        if issue_type == "viewport":
            location["selector"] = "head > meta[name='viewport']"
            location["html_snippet"] = "Missing viewport meta tag"
        elif issue_type == "responsive_images":
            location["selector"] = "img"
            location["html_snippet"] = "Images without srcset or responsive attributes"
        elif issue_type == "touch_targets":
            location["selector"] = "button, a, input[type='submit']"
            location["html_snippet"] = f"Touch targets: {details}"
        elif issue_type == "navigation":
            location["selector"] = "nav"
            location["html_snippet"] = f"Navigation: {details}"
        elif issue_type == "readability":
            location["selector"] = "body"
            location["html_snippet"] = f"Content readability: {details}"
        elif issue_type == "layout":
            location["selector"] = "img"
            location["html_snippet"] = f"Layout stability: {details}"
        elif issue_type == "forms":
            location["selector"] = "form, input, textarea, select"
            location["html_snippet"] = f"Form usability: {details}"
        else:
            location["selector"] = "general"
            location["html_snippet"] = f"UX issue: {details}"
        
        return location
    
    def _generate_ux_recommendations(self, mobile_results: Dict, touch_results: Dict, nav_results: Dict,
                                   readability_results: Dict, layout_results: Dict, form_results: Dict, url: str) -> tuple:
        """Generate UX issues and recommendations"""
        issues = []
        recommendations = []
        
        # Mobile responsiveness issues
        for issue in mobile_results.get("issues", []):
            issues.append({
                "description": f"Mobile: {issue}",
                "location": self._get_ux_location(url, "viewport", issue),
                "severity": "high",
                "help": "Optimize for mobile devices"
            })
        
        if not mobile_results.get("viewport_configured", False):
            recommendations.append("Add viewport meta tag for mobile optimization")
        
        if mobile_results.get("responsive_images", 0) == 0:
            recommendations.append("Implement responsive images with srcset")
        
        # Touch target issues
        for issue in touch_results.get("issues", []):
            issues.append({
                "description": f"Touch targets: {issue}",
                "location": self._get_ux_location(url, "touch_targets", issue),
                "severity": "medium",
                "help": "Ensure touch targets are at least 44px in size"
            })
        
        if touch_results.get("potential_small_targets", 0) > 0:
            recommendations.append("Ensure touch targets are at least 44px in size")
        
        # Navigation issues
        for issue in nav_results.get("issues", []):
            issues.append({
                "description": f"Navigation: {issue}",
                "location": self._get_ux_location(url, "navigation", issue),
                "severity": "medium",
                "help": "Improve navigation structure"
            })
        
        if not nav_results.get("mobile_navigation", False):
            recommendations.append("Implement mobile-friendly navigation pattern")
        
        # Readability issues
        for issue in readability_results.get("issues", []):
            issues.append({
                "description": f"Readability: {issue}",
                "location": self._get_ux_location(url, "readability", issue),
                "severity": "medium",
                "help": "Improve content readability"
            })
        
        if readability_results.get("word_count", 0) < 100:
            recommendations.append("Add more descriptive content for better user understanding")
        
        # Layout stability issues
        for issue in layout_results.get("issues", []):
            issues.append({
                "description": f"Layout: {issue}",
                "location": self._get_ux_location(url, "layout", issue),
                "severity": "medium",
                "help": "Improve layout stability"
            })
        
        if layout_results.get("images_without_dimensions", 0) > 0:
            recommendations.append("Add width and height attributes to images")
        
        # Form usability issues
        for issue in form_results.get("issues", []):
            issues.append({
                "description": f"Forms: {issue}",
                "location": self._get_ux_location(url, "forms", issue),
                "severity": "medium",
                "help": "Improve form usability"
            })
        
        if form_results.get("inputs_without_labels", 0) > 0:
            recommendations.append("Add labels to all form inputs")
        
        return issues, recommendations