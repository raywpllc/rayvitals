"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog
import redis

from app.core.database import get_async_session
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "rayvitals-backend"}


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_async_session)):
    """Detailed health check with dependency verification"""
    health_status = {
        "status": "healthy",
        "service": "rayvitals-backend",
        "version": settings.VERSION,
        "checks": {}
    }
    
    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy", "response_time": "< 1s"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
        redis_client.close()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Supabase check (disabled for now)
    health_status["checks"]["supabase"] = {"status": "disabled", "note": "Using direct PostgreSQL connection"}
    
    # AI Service check (if configured)
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            # Simple test query
            response = model.generate_content("Hello")
            health_status["checks"]["gemini_ai"] = {"status": "healthy"}
        except Exception as e:
            logger.error("Gemini AI health check failed", error=str(e))
            health_status["checks"]["gemini_ai"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "unhealthy"
    else:
        health_status["checks"]["gemini_ai"] = {"status": "not_configured"}
    
    return health_status