"""
Security scanning service
"""

import asyncio
import ssl
import socket
from typing import Dict, Any, List
from urllib.parse import urlparse
import httpx
import structlog

logger = structlog.get_logger()


class SecurityScanner:
    """Security analysis service"""
    
    def __init__(self):
        self.timeout = 30.0
    
    async def scan_website(self, url: str) -> Dict[str, Any]:
        """Perform comprehensive security scan"""
        results = {
            "score": 0,
            "issues": [],
            "recommendations": [],
            "ssl_info": {},
            "security_headers": {},
            "vulnerabilities": []
        }
        
        try:
            # SSL/TLS analysis
            ssl_results = await self._check_ssl(url)
            results["ssl_info"] = ssl_results
            
            # Security headers analysis
            headers_results = await self._check_security_headers(url)
            results["security_headers"] = headers_results
            
            # Basic vulnerability checks
            vuln_results = await self._basic_vulnerability_scan(url)
            results["vulnerabilities"] = vuln_results
            
            # Calculate overall security score
            results["score"] = self._calculate_security_score(ssl_results, headers_results, vuln_results)
            
            # Generate issues and recommendations
            results["issues"], results["recommendations"] = self._generate_security_recommendations(
                ssl_results, headers_results, vuln_results
            )
            
        except Exception as e:
            logger.error("Security scan failed", error=str(e), url=url)
            results["score"] = 0
            results["issues"].append(f"Security scan failed: {str(e)}")
        
        return results
    
    async def _check_ssl(self, url: str) -> Dict[str, Any]:
        """Check SSL/TLS configuration"""
        ssl_info = {
            "enabled": False,
            "version": None,
            "cipher": None,
            "certificate_valid": False,
            "expires_days": None,
            "issuer": None,
            "subject": None,
            "score": 0
        }
        
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            if parsed_url.scheme != "https":
                ssl_info["score"] = 0
                return ssl_info
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate info
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    ssl_info["enabled"] = True
                    ssl_info["version"] = ssock.version()
                    ssl_info["cipher"] = ssock.cipher()
                    
                    # Get certificate
                    cert = ssock.getpeercert()
                    ssl_info["certificate_valid"] = True
                    ssl_info["subject"] = dict(x[0] for x in cert['subject'])
                    ssl_info["issuer"] = dict(x[0] for x in cert['issuer'])
                    
                    # Certificate expiry
                    import datetime
                    expire_date = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_to_expire = (expire_date - datetime.datetime.now()).days
                    ssl_info["expires_days"] = days_to_expire
                    
                    # Calculate SSL score
                    if days_to_expire > 30:
                        ssl_info["score"] = 100
                    elif days_to_expire > 7:
                        ssl_info["score"] = 80
                    elif days_to_expire > 0:
                        ssl_info["score"] = 60
                    else:
                        ssl_info["score"] = 0
                        
        except Exception as e:
            logger.error("SSL check failed", error=str(e), url=url)
            ssl_info["score"] = 0
        
        return ssl_info
    
    async def _check_security_headers(self, url: str) -> Dict[str, Any]:
        """Check security headers"""
        headers_info = {
            "headers": {},
            "score": 0,
            "missing_headers": []
        }
        
        # Important security headers
        security_headers = {
            "strict-transport-security": "HSTS",
            "x-content-type-options": "Content Type Options",
            "x-frame-options": "Frame Options",
            "x-xss-protection": "XSS Protection",
            "content-security-policy": "Content Security Policy",
            "referrer-policy": "Referrer Policy"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(url, follow_redirects=True)
                
                score = 0
                present_headers = {}
                missing_headers = []
                
                for header_name, header_desc in security_headers.items():
                    if header_name in response.headers:
                        present_headers[header_name] = response.headers[header_name]
                        score += 16.67  # 100/6 headers
                    else:
                        missing_headers.append(header_desc)
                
                headers_info["headers"] = present_headers
                headers_info["missing_headers"] = missing_headers
                headers_info["score"] = round(score, 1)
                
        except Exception as e:
            logger.error("Security headers check failed", error=str(e), url=url)
            headers_info["score"] = 0
        
        return headers_info
    
    async def _basic_vulnerability_scan(self, url: str) -> List[Dict[str, Any]]:
        """Basic vulnerability scanning"""
        vulnerabilities = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check for common vulnerabilities
                
                # Server information disclosure
                response = await client.get(url)
                if "server" in response.headers:
                    server_header = response.headers["server"]
                    if any(server in server_header.lower() for server in ["apache", "nginx", "iis"]):
                        vulnerabilities.append({
                            "type": "information_disclosure",
                            "severity": "low",
                            "description": "Server version disclosed in headers",
                            "details": f"Server: {server_header}"
                        })
                
                # Check for common paths
                common_paths = [
                    "/.git/config",
                    "/admin",
                    "/wp-admin",
                    "/phpmyadmin",
                    "/.env"
                ]
                
                for path in common_paths:
                    try:
                        test_response = await client.get(url.rstrip("/") + path, timeout=5.0)
                        if test_response.status_code == 200:
                            vulnerabilities.append({
                                "type": "exposed_path",
                                "severity": "medium",
                                "description": f"Exposed path: {path}",
                                "details": f"HTTP {test_response.status_code} response"
                            })
                    except:
                        pass  # Path not accessible, which is good
                
        except Exception as e:
            logger.error("Vulnerability scan failed", error=str(e), url=url)
        
        return vulnerabilities
    
    def _calculate_security_score(self, ssl_info: Dict, headers_info: Dict, vulnerabilities: List) -> float:
        """Calculate overall security score"""
        ssl_score = ssl_info.get("score", 0)
        headers_score = headers_info.get("score", 0)
        
        # Deduct points for vulnerabilities
        vuln_penalty = 0
        for vuln in vulnerabilities:
            if vuln["severity"] == "high":
                vuln_penalty += 30
            elif vuln["severity"] == "medium":
                vuln_penalty += 15
            elif vuln["severity"] == "low":
                vuln_penalty += 5
        
        # Weighted score: SSL 50%, Headers 50%, minus vulnerabilities
        overall_score = (ssl_score * 0.5) + (headers_score * 0.5) - vuln_penalty
        return max(0, min(100, round(overall_score, 1)))
    
    def _generate_security_recommendations(self, ssl_info: Dict, headers_info: Dict, vulnerabilities: List) -> tuple:
        """Generate security issues and recommendations"""
        issues = []
        recommendations = []
        
        # SSL issues
        if not ssl_info.get("enabled", False):
            issues.append("SSL/HTTPS not enabled")
            recommendations.append("Enable SSL/HTTPS for secure connections")
        elif ssl_info.get("expires_days", 0) < 30:
            issues.append(f"SSL certificate expires in {ssl_info.get('expires_days', 0)} days")
            recommendations.append("Renew SSL certificate")
        
        # Security headers
        for missing_header in headers_info.get("missing_headers", []):
            issues.append(f"Missing security header: {missing_header}")
            recommendations.append(f"Add {missing_header} header")
        
        # Vulnerabilities
        for vuln in vulnerabilities:
            issues.append(f"{vuln['severity'].title()} vulnerability: {vuln['description']}")
            if vuln['type'] == 'information_disclosure':
                recommendations.append("Remove or obscure server version information")
            elif vuln['type'] == 'exposed_path':
                recommendations.append(f"Secure or remove exposed path: {vuln['details']}")
        
        return issues, recommendations