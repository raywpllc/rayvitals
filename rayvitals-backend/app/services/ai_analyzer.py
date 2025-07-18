"""
AI Analysis service using Google Gemini
"""

import asyncio
from typing import Dict, Any, Optional, List
import structlog
import google.generativeai as genai

from app.core.config import settings

logger = structlog.get_logger()


class AIAnalyzer:
    """AI analysis service for website intelligence"""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not configured - AI analysis disabled")
    
    async def generate_summary(self, url: str, audit_results: Dict[str, Any], scores: Dict[str, float]) -> str:
        """Generate AI-powered business intelligence summary"""
        if not self.model:
            return self._generate_fallback_summary(url, audit_results, scores)
        
        try:
            # Create comprehensive prompt based on audit results
            prompt = self._create_analysis_prompt(url, audit_results, scores)
            
            # Generate AI summary
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info("AI summary generated successfully", url=url)
                return response.text
            else:
                logger.warning("Empty AI response, using fallback", url=url)
                return self._generate_fallback_summary(url, audit_results, scores)
                
        except Exception as e:
            logger.error("AI analysis failed", error=str(e), url=url)
            return self._generate_fallback_summary(url, audit_results, scores)
    
    def _extract_issue_descriptions(self, issues: List[Any]) -> List[str]:
        """Extract string descriptions from issues array that may contain both strings and objects"""
        descriptions = []
        for issue in issues:
            if isinstance(issue, str):
                descriptions.append(issue)
            elif isinstance(issue, dict) and 'description' in issue:
                descriptions.append(issue['description'])
            elif isinstance(issue, dict) and 'message' in issue:
                descriptions.append(issue['message'])
            else:
                # Convert other objects to string representation
                descriptions.append(str(issue))
        return descriptions
    
    def _create_analysis_prompt(self, url: str, audit_results: Dict[str, Any], scores: Dict[str, float]) -> str:
        """Create comprehensive analysis prompt for Gemini"""
        
        # Extract key metrics
        security_score = scores.get("security", 0)
        performance_score = scores.get("performance", 0)
        seo_score = scores.get("seo", 0)
        overall_score = scores.get("overall", 0)
        
        # Get specific issues and ensure they're strings
        security_issues = self._extract_issue_descriptions(audit_results.get("security", {}).get("issues", []))
        performance_issues = self._extract_issue_descriptions(audit_results.get("performance", {}).get("issues", []))
        seo_issues = self._extract_issue_descriptions(audit_results.get("seo", {}).get("issues", []))
        
        # Get performance metrics
        response_time = audit_results.get("performance", {}).get("response_time", 0)
        page_size = audit_results.get("performance", {}).get("page_size", 0)
        
        # Build prompt
        prompt = f"""
Analyze this website audit data for {url} and provide executive-level business insights:

OVERALL PERFORMANCE:
- Overall Score: {overall_score}/100
- Security Score: {security_score}/100
- Performance Score: {performance_score}/100
- SEO Score: {seo_score}/100

PERFORMANCE METRICS:
- Response Time: {response_time}ms
- Page Size: {page_size / 1024 if page_size else 0:.1f}KB

CRITICAL ISSUES IDENTIFIED:
Security Issues: {', '.join(security_issues[:3]) if security_issues else 'None detected'}
Performance Issues: {', '.join(performance_issues[:3]) if performance_issues else 'None detected'}
SEO Issues: {', '.join(seo_issues[:3]) if seo_issues else 'None detected'}

ANALYSIS REQUIREMENTS:
Provide a concise executive summary (2 paragraphs) that includes:

1. **Overall Assessment**: Provide a balanced evaluation of the website's technical health and user experience. Focus on opportunities for improvement rather than criticizing current performance. Avoid specific revenue predictions or loss estimates.

2. **Priority Recommendations**: List the top 3 most critical issues to address first as bullet points, explaining why each is important for user experience and site performance.

Focus on constructive guidance and actionable improvements. Use clear, professional language suitable for business decision-makers.
"""
        
        return prompt
    
    def _generate_fallback_summary(self, url: str, audit_results: Dict[str, Any], scores: Dict[str, float]) -> str:
        """Generate fallback summary when AI is unavailable"""
        overall_score = scores.get("overall", 0)
        security_score = scores.get("security", 0)
        performance_score = scores.get("performance", 0)
        seo_score = scores.get("seo", 0)
        
        # Determine overall health
        if overall_score >= 80:
            health_status = "excellent"
            impact_level = "minimal"
        elif overall_score >= 60:
            health_status = "good"
            impact_level = "moderate"
        elif overall_score >= 40:
            health_status = "fair"
            impact_level = "significant"
        else:
            health_status = "poor"
            impact_level = "critical"
        
        # Identify critical areas
        critical_areas = []
        if security_score < 60:
            critical_areas.append("security vulnerabilities")
        if performance_score < 60:
            critical_areas.append("performance issues")
        if seo_score < 60:
            critical_areas.append("SEO problems")
        
        # Generate summary
        summary = f"""**Website Health Assessment**

Your website scored {overall_score}/100 overall, indicating {health_status} technical health. There are opportunities to enhance user experience and site performance.

**Priority Areas for Improvement:**
{', '.join(critical_areas).title() if critical_areas else 'No critical issues identified'}

**Key Recommendations:**
• Security Score ({security_score}/100): {'Consider implementing additional security headers for enhanced protection' if security_score < 60 else '✅ Strong security foundation'}
• Performance Score ({performance_score}/100): {'Optimize loading speeds to improve user experience' if performance_score < 60 else '✅ Good performance supporting user experience'}  
• SEO Score ({seo_score}/100): {'Improve technical SEO elements for better search visibility' if seo_score < 60 else '✅ Solid SEO foundation'}

**Next Steps:**
Focus on addressing the highest-impact improvements first for the best results.

*Note: This is a basic analysis. Enable AI analysis for detailed business intelligence and strategic recommendations.*
"""
        
        return summary
    
    async def generate_competitive_analysis(self, url: str, audit_results: Dict[str, Any], industry: str = "general") -> str:
        """Generate competitive analysis (Pro tier feature)"""
        if not self.model:
            return "AI competitive analysis requires Gemini API configuration."
        
        try:
            prompt = f"""
Analyze this website audit data for {url} in the {industry} industry and provide competitive intelligence:

AUDIT RESULTS: {audit_results}

Provide:
1. Industry benchmark comparison
2. Competitive positioning analysis
3. Strategic recommendations for gaining competitive advantage
4. Market opportunity assessment

Focus on actionable insights that can drive business growth.
"""
            
            response = self.model.generate_content(prompt)
            return response.text if response.text else "Competitive analysis unavailable."
            
        except Exception as e:
            logger.error("Competitive analysis failed", error=str(e), url=url)
            return "Competitive analysis temporarily unavailable."
    
    async def generate_recommendations(self, url: str, audit_results: Dict[str, Any], priority: str = "high") -> Dict[str, Any]:
        """Generate prioritized recommendations"""
        if not self.model:
            return self._generate_fallback_recommendations(audit_results)
        
        try:
            prompt = f"""
Based on this website audit data for {url}, provide specific, actionable recommendations:

AUDIT DATA: {audit_results}

Generate recommendations in JSON format with:
- category: security/performance/seo/ux
- priority: high/medium/low
- effort: low/medium/high
- impact: low/medium/high
- description: specific action to take
- business_benefit: expected business outcome

Focus on {priority} priority items with clear ROI.
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response (simplified for now)
            return {"recommendations": response.text if response.text else "No recommendations available"}
            
        except Exception as e:
            logger.error("Recommendations generation failed", error=str(e), url=url)
            return self._generate_fallback_recommendations(audit_results)
    
    def _generate_fallback_recommendations(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic recommendations without AI"""
        recommendations = []
        
        # Security recommendations
        security_issues = audit_results.get("security", {}).get("issues", [])
        for issue in security_issues[:2]:
            recommendations.append({
                "category": "security",
                "priority": "high",
                "description": f"Address: {issue}",
                "business_benefit": "Improve user trust and SEO rankings"
            })
        
        # Performance recommendations
        performance_issues = audit_results.get("performance", {}).get("issues", [])
        for issue in performance_issues[:2]:
            recommendations.append({
                "category": "performance",
                "priority": "high",
                "description": f"Fix: {issue}",
                "business_benefit": "Improve conversion rates and user experience"
            })
        
        return {"recommendations": recommendations}