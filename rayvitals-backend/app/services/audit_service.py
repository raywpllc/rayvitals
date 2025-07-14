"""
Audit service for website analysis
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import ssl
import socket
import structlog
import httpx
import uuid
from sqlalchemy import select

from app.core.database import get_session_factory
from app.models.audit import AuditRequest, AuditResult, AuditMetrics
from app.services.security_scanner import SecurityScanner
from app.services.performance_scanner import PerformanceScanner
from app.services.ai_analyzer import AIAnalyzer

logger = structlog.get_logger()


class AuditService:
    """Main audit service orchestrator"""
    
    def __init__(self):
        self.security_scanner = SecurityScanner()
        self.performance_scanner = PerformanceScanner()
        self.ai_analyzer = AIAnalyzer()
    
    async def process_audit(self, audit_id: str, url: str) -> None:
        """Process a complete website audit"""
        start_time = time.time()
        
        try:
            session_factory = get_session_factory()
            if not session_factory:
                raise RuntimeError("Database not configured - cannot process audit")
                
            async with session_factory() as db:
                # Update status to processing
                stmt = select(AuditRequest).where(AuditRequest.id == uuid.UUID(audit_id))
                result = await db.execute(stmt)
                audit_request = result.scalar_one_or_none()
                
                if not audit_request:
                    raise ValueError(f"Audit request {audit_id} not found")
                
                audit_request.status = "processing"
                audit_request.updated_at = datetime.utcnow()
                await db.commit()
                
                logger.info("Starting audit processing", audit_id=audit_id, url=url)
                
                # Validate URL
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL format")
                
                # Run all audit components
                audit_results = {}
                
                # Security analysis
                logger.info("Running security analysis", audit_id=audit_id)
                security_results = await self.security_scanner.scan_website(url)
                audit_results["security"] = security_results
                
                # Performance analysis
                logger.info("Running performance analysis", audit_id=audit_id)
                performance_results = await self.performance_scanner.scan_website(url)
                audit_results["performance"] = performance_results
                
                # Basic SEO analysis
                logger.info("Running basic SEO analysis", audit_id=audit_id)
                seo_results = await self._basic_seo_analysis(url)
                audit_results["seo"] = seo_results
                
                # Calculate scores
                scores = self._calculate_scores(audit_results)
                
                # Generate AI summary
                logger.info("Generating AI summary", audit_id=audit_id)
                ai_summary = await self.ai_analyzer.generate_summary(url, audit_results, scores)
                
                # Save results
                processing_time = time.time() - start_time
                
                audit_request.status = "completed"
                audit_request.completed_at = datetime.utcnow()
                audit_request.processing_time = processing_time
                audit_request.results = audit_results
                audit_request.ai_summary = ai_summary
                audit_request.overall_score = scores["overall"]
                audit_request.security_score = scores["security"]
                audit_request.performance_score = scores["performance"]
                audit_request.seo_score = scores["seo"]
                audit_request.ux_score = scores["ux"]
                audit_request.accessibility_score = scores["accessibility"]
                
                await db.commit()
                
                # Save detailed results
                await self._save_detailed_results(db, audit_id, audit_results, scores)
                
                logger.info("Audit completed successfully", 
                           audit_id=audit_id, 
                           processing_time=processing_time,
                           overall_score=scores["overall"])
                
        except Exception as e:
            logger.error("Audit processing failed", error=str(e), audit_id=audit_id)
            
            # Update audit status to failed
            session_factory = get_session_factory()
            if session_factory:
                async with session_factory() as db:
                    stmt = select(AuditRequest).where(AuditRequest.id == uuid.UUID(audit_id))
                    result = await db.execute(stmt)
                    audit_request = result.scalar_one_or_none()
                    
                    if audit_request:
                        audit_request.status = "failed"
                        audit_request.error_message = str(e)
                        audit_request.updated_at = datetime.utcnow()
                        audit_request.processing_time = time.time() - start_time
                        await db.commit()
            
            raise
    
    async def _basic_seo_analysis(self, url: str) -> Dict[str, Any]:
        """Basic SEO analysis"""
        results = {
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    results["issues"].append(f"HTTP status: {response.status_code}")
                    results["score"] = 20
                    return results
                
                html_content = response.text
                
                # Basic SEO checks
                score = 100
                
                # Title tag
                if "<title>" not in html_content.lower():
                    results["issues"].append("Missing title tag")
                    results["recommendations"].append("Add a descriptive title tag")
                    score -= 20
                
                # Meta description
                if 'name="description"' not in html_content.lower():
                    results["issues"].append("Missing meta description")
                    results["recommendations"].append("Add a meta description")
                    score -= 15
                
                # H1 tag
                if "<h1>" not in html_content.lower():
                    results["issues"].append("Missing H1 tag")
                    results["recommendations"].append("Add an H1 tag")
                    score -= 10
                
                # Mobile viewport
                if 'name="viewport"' not in html_content.lower():
                    results["issues"].append("Missing viewport meta tag")
                    results["recommendations"].append("Add viewport meta tag for mobile")
                    score -= 15
                
                results["score"] = max(0, score)
                
        except Exception as e:
            logger.error("SEO analysis failed", error=str(e), url=url)
            results["score"] = 0
            results["issues"].append(f"Analysis failed: {str(e)}")
        
        return results
    
    def _calculate_scores(self, audit_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate category and overall scores"""
        scores = {
            "security": audit_results.get("security", {}).get("score", 0),
            "performance": audit_results.get("performance", {}).get("score", 0),
            "seo": audit_results.get("seo", {}).get("score", 0),
            "ux": 85,  # Placeholder
            "accessibility": 80,  # Placeholder
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
    
    async def _save_detailed_results(self, db, audit_id: str, audit_results: Dict[str, Any], scores: Dict[str, float]):
        """Save detailed audit results"""
        try:
            for category, results in audit_results.items():
                if category in scores:
                    audit_result = AuditResult(
                        audit_id=uuid.UUID(audit_id),
                        category=category,
                        raw_data=results,
                        score=scores[category],
                        issues=results.get("issues", []),
                        recommendations=results.get("recommendations", [])
                    )
                    db.add(audit_result)
            
            await db.commit()
            
        except Exception as e:
            logger.error("Failed to save detailed results", error=str(e), audit_id=audit_id)