#!/usr/bin/env python3
"""
Simple web interface for testing RayVitals scanners
"""

import asyncio
import json
import time
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner
from app.services.security_scanner import SecurityScanner
from app.services.performance_scanner import PerformanceScanner

class AuditHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>RayVitals Local Test</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .container { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                    input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
                    button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                    button:hover { background: #0056b3; }
                    .results { margin-top: 20px; padding: 15px; background: white; border-radius: 4px; }
                    .score { font-size: 24px; font-weight: bold; margin: 10px 0; }
                    .issue { margin: 5px 0; padding: 5px; background: #fff3cd; border-left: 3px solid #ffc107; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎯 RayVitals Local Test Interface</h1>
                    <form onsubmit="runAudit(event)">
                        <input type="url" id="url" placeholder="https://example.com" required>
                        <button type="submit">Run Audit</button>
                    </form>
                    <div id="results"></div>
                </div>
                
                <script>
                    function runAudit(event) {
                        event.preventDefault();
                        const url = document.getElementById('url').value;
                        const results = document.getElementById('results');
                        
                        results.innerHTML = '<p>🔍 Running audit... Please wait 30-60 seconds.</p>';
                        
                        fetch('/audit', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({url: url})
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                displayResults(data);
                            } else {
                                results.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                            }
                        })
                        .catch(error => {
                            results.innerHTML = `<div class="error">Network error: ${error}</div>`;
                        });
                    }
                    
                    function displayResults(data) {
                        const results = document.getElementById('results');
                        let html = `
                            <div class="results">
                                <h2>Results for ${data.url}</h2>
                                <div class="score">Overall Score: ${data.scores.overall}</div>
                                <div>Security: ${data.scores.security}</div>
                                <div>Performance: ${data.scores.performance}</div>
                                <div>UX: ${data.scores.ux}</div>
                                <div>Accessibility: ${data.scores.accessibility}</div>
                                <div>Processing Time: ${data.processing_time}s</div>
                                <h3>Issues Found:</h3>
                        `;
                        
                        for (const [category, categoryData] of Object.entries(data.results)) {
                            const issues = categoryData.issues || [];
                            if (issues.length > 0) {
                                html += `<h4>${category.toUpperCase()}</h4>`;
                                issues.slice(0, 3).forEach(issue => {
                                    html += `<div class="issue">${issue}</div>`;
                                });
                            }
                        }
                        
                        html += '</div>';
                        results.innerHTML = html;
                    }
                </script>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/audit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                if not url:
                    self.send_error_response({'error': 'URL is required'})
                    return
                
                # Run audit in background
                result = asyncio.run(self.run_audit(url))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_error_response({'error': str(e)})
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_error_response(self, error_data):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_data).encode())
    
    async def run_audit(self, url):
        try:
            start_time = time.time()
            
            # Initialize scanners
            security_scanner = SecurityScanner()
            performance_scanner = PerformanceScanner()
            accessibility_scanner = AccessibilityScanner()
            ux_scanner = UXScanner()
            
            # Run scans
            security_results = await security_scanner.scan_website(url)
            performance_results = await performance_scanner.scan_website(url)
            ux_results = await ux_scanner.scan_website(url)
            accessibility_results = await accessibility_scanner.scan_website(url)
            
            # Calculate scores
            scores = {
                "security": security_results.get("score", 0),
                "performance": performance_results.get("score", 0),
                "ux": ux_results.get("score", 0),
                "accessibility": accessibility_results.get("score", 0),
            }
            
            # Calculate overall score
            weights = {"security": 0.25, "performance": 0.25, "ux": 0.3, "accessibility": 0.2}
            overall_score = sum(scores[category] * weights[category] for category in scores)
            scores["overall"] = round(overall_score, 1)
            
            processing_time = round(time.time() - start_time, 2)
            
            return {
                "status": "success",
                "url": url,
                "scores": scores,
                "results": {
                    "security": security_results,
                    "performance": performance_results,
                    "ux": ux_results,
                    "accessibility": accessibility_results,
                },
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

def run_server():
    server_address = ('', 8002)
    httpd = HTTPServer(server_address, AuditHandler)
    print("🚀 RayVitals Local Test Server Starting...")
    print("📱 Access the test interface at: http://localhost:8002")
    print("💡 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    run_server()