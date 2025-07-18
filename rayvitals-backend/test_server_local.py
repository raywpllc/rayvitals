#!/usr/bin/env python3
"""
Local test server for RayVitals scanners without database
"""

import asyncio
import json
import time
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.services.security_scanner import SecurityScanner
from app.services.performance_scanner import PerformanceScanner
from app.services.accessibility_scanner import AccessibilityScanner
from app.services.ux_scanner import UXScanner


class AuditRequest(BaseModel):
    url: str


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
        
        audit_results = {}
        
        try:
            # Security analysis
            security_results = await self.security_scanner.scan_website(url)
            audit_results["security"] = security_results
            
            # Performance analysis
            performance_results = await self.performance_scanner.scan_website(url)
            audit_results["performance"] = performance_results
            
            # UX analysis
            ux_results = await self.ux_scanner.scan_website(url)
            audit_results["ux"] = ux_results
            
            # Accessibility analysis
            accessibility_results = await self.accessibility_scanner.scan_website(url)
            audit_results["accessibility"] = accessibility_results
            
            # Calculate scores
            scores = self._calculate_scores(audit_results)
            
            processing_time = time.time() - start_time
            
            return {
                "status": "completed",
                "scores": scores,
                "results": audit_results,
                "processing_time": processing_time,
                "url": url
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "url": url
            }
    
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


# Create FastAPI app
app = FastAPI(title="RayVitals Local Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize audit service
audit_service = LocalAuditService()


@app.get("/", response_class=HTMLResponse)
async def get_test_interface():
    """Serve the test interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RayVitals Local Test Interface</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input[type="url"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                box-sizing: border-box;
            }
            button {
                background-color: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            button:hover {
                background-color: #0056b3;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .loading {
                text-align: center;
                color: #666;
                margin-top: 20px;
            }
            .results {
                margin-top: 30px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .score-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .score-card {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .score-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .score-label {
                color: #666;
                font-size: 0.9em;
            }
            .issues {
                margin-top: 20px;
            }
            .issue-category {
                margin-bottom: 15px;
                padding: 10px;
                background-color: white;
                border-radius: 5px;
                border-left: 4px solid #dc3545;
            }
            .issue-category h4 {
                margin-top: 0;
                color: #dc3545;
            }
            .issue-list {
                list-style-type: none;
                padding: 0;
            }
            .issue-list li {
                padding: 5px 0;
                border-bottom: 1px solid #eee;
            }
            .issue-list li:last-child {
                border-bottom: none;
            }
            .error {
                color: #dc3545;
                background-color: #f8d7da;
                padding: 10px;
                border-radius: 5px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 RayVitals Local Test Interface</h1>
            
            <div class="form-group">
                <label for="url">Website URL to Audit:</label>
                <input type="url" id="url" placeholder="https://example.com" value="https://example.com">
            </div>
            
            <button onclick="runAudit()" id="auditBtn">Run Audit</button>
            
            <div id="loading" class="loading" style="display: none;">
                <p>🔍 Running audit... This may take 30-60 seconds.</p>
            </div>
            
            <div id="results" class="results" style="display: none;"></div>
        </div>

        <script>
            async function runAudit() {
                const url = document.getElementById('url').value;
                const auditBtn = document.getElementById('auditBtn');
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                // Show loading state
                auditBtn.disabled = true;
                loading.style.display = 'block';
                results.style.display = 'none';
                
                try {
                    const response = await fetch('/api/audit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url: url })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'completed') {
                        displayResults(data);
                    } else {
                        displayError(data.error || 'Audit failed');
                    }
                } catch (error) {
                    displayError('Network error: ' + error.message);
                } finally {
                    auditBtn.disabled = false;
                    loading.style.display = 'none';
                }
            }
            
            function displayResults(data) {
                const results = document.getElementById('results');
                
                let html = `
                    <h2>Audit Results for ${data.url}</h2>
                    <p><strong>Processing Time:</strong> ${data.processing_time.toFixed(2)}s</p>
                    
                    <div class="score-grid">
                        <div class="score-card">
                            <div class="score-value" style="color: ${getScoreColor(data.scores.overall)}">${data.scores.overall}</div>
                            <div class="score-label">Overall Score</div>
                        </div>
                        <div class="score-card">
                            <div class="score-value" style="color: ${getScoreColor(data.scores.security)}">${data.scores.security}</div>
                            <div class="score-label">Security</div>
                        </div>
                        <div class="score-card">
                            <div class="score-value" style="color: ${getScoreColor(data.scores.performance)}">${data.scores.performance}</div>
                            <div class="score-label">Performance</div>
                        </div>
                        <div class="score-card">
                            <div class="score-value" style="color: ${getScoreColor(data.scores.ux)}">${data.scores.ux}</div>
                            <div class="score-label">UX</div>
                        </div>
                        <div class="score-card">
                            <div class="score-value" style="color: ${getScoreColor(data.scores.accessibility)}">${data.scores.accessibility}</div>
                            <div class="score-label">Accessibility</div>
                        </div>
                    </div>
                    
                    <div class="issues">
                        <h3>Issues Found:</h3>
                `;
                
                // Display issues by category
                for (const [category, categoryData] of Object.entries(data.results)) {
                    const issues = categoryData.issues || [];
                    if (issues.length > 0) {
                        html += `
                            <div class="issue-category">
                                <h4>${category.toUpperCase()}</h4>
                                <ul class="issue-list">
                        `;
                        
                        issues.slice(0, 5).forEach(issue => {
                            html += `<li>${issue}</li>`;
                        });
                        
                        if (issues.length > 5) {
                            html += `<li>... and ${issues.length - 5} more issues</li>`;
                        }
                        
                        html += `</ul></div>`;
                    }
                }
                
                html += `</div>`;
                
                results.innerHTML = html;
                results.style.display = 'block';
            }
            
            function displayError(error) {
                const results = document.getElementById('results');
                results.innerHTML = `<div class="error">Error: ${error}</div>`;
                results.style.display = 'block';
            }
            
            function getScoreColor(score) {
                if (score >= 80) return '#28a745';
                if (score >= 60) return '#ffc107';
                return '#dc3545';
            }
            
            // Allow Enter key to trigger audit
            document.getElementById('url').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    runAudit();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/api/audit")
async def run_audit_endpoint(request: AuditRequest):
    """Run audit endpoint"""
    try:
        result = await audit_service.run_audit(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RayVitals Local Test Server"}


if __name__ == "__main__":
    print("🚀 Starting RayVitals Local Test Server...")
    print("📱 Access the test interface at: http://localhost:8001")
    print("🔗 API endpoint: http://localhost:8001/api/audit")
    print("💡 Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)