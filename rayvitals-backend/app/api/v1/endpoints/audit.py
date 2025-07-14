"""
Audit endpoints for website analysis
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
import structlog
import uuid

from app.core.database import get_async_session
from app.models.audit import AuditRequest
from app.services.audit_service import AuditService

logger = structlog.get_logger()
router = APIRouter()


class AuditStartRequest(BaseModel):
    """Request model for starting an audit"""
    url: HttpUrl
    site_token: Optional[str] = None
    user_id: Optional[str] = None


class AuditStatusResponse(BaseModel):
    """Response model for audit status"""
    id: str
    url: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Scores
    overall_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    seo_score: Optional[float] = None
    ux_score: Optional[float] = None
    accessibility_score: Optional[float] = None


class AuditResultResponse(BaseModel):
    """Response model for audit results"""
    id: str
    url: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    
    # Scores
    overall_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    seo_score: Optional[float] = None
    ux_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    
    # Results
    results: Optional[dict] = None
    ai_summary: Optional[str] = None


@router.post("/start", response_model=dict)
async def start_audit(
    request: AuditStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Start a new website audit"""
    try:
        # Create audit request
        audit_request = AuditRequest(
            url=str(request.url),
            site_token=request.site_token,
            user_id=request.user_id,
            status="pending"
        )
        
        db.add(audit_request)
        await db.commit()
        await db.refresh(audit_request)
        
        # Start background audit processing
        background_tasks.add_task(
            process_audit_background,
            str(audit_request.id),
            str(request.url)
        )
        
        logger.info("Audit started", audit_id=str(audit_request.id), url=str(request.url))
        
        return {
            "audit_id": str(audit_request.id),
            "status": "pending",
            "message": "Audit started successfully"
        }
        
    except RuntimeError as e:
        if "Database not configured" in str(e):
            logger.warning("Audit failed - database not configured", url=str(request.url))
            raise HTTPException(
                status_code=503, 
                detail="Database not configured. Please set up Supabase database connection to start audits."
            )
        else:
            logger.error("Failed to start audit", error=str(e), url=str(request.url))
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Failed to start audit", error=str(e), url=str(request.url))
        raise HTTPException(status_code=500, detail=f"Failed to start audit: {str(e)}")


@router.post("/async", response_model=dict)
async def start_async_audit(request: AuditStartRequest):
    """Start an async audit using Celery"""
    try:
        from app.tasks.audit_tasks import process_audit_task
        
        # Generate unique audit ID
        audit_id = str(uuid.uuid4())
        
        # Start Celery task
        task = process_audit_task.delay(audit_id, str(request.url))
        
        logger.info("Async audit started", audit_id=audit_id, task_id=task.id, url=str(request.url))
        
        return {
            "audit_id": audit_id,
            "task_id": task.id,
            "status": "pending",
            "message": "Async audit started successfully"
        }
        
    except Exception as e:
        logger.error("Failed to start async audit", error=str(e), url=str(request.url))
        raise HTTPException(status_code=500, detail=f"Failed to start async audit: {str(e)}")


@router.get("/task/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    """Get Celery task status"""
    try:
        from app.core.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "status": "in_progress",
                "current": task.info.get("current", 0),
                "total": task.info.get("total", 100),
                "message": task.info.get("status", "Processing...")
            }
        elif task.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "status": "completed",
                "result": task.result
            }
        else:
            response = {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        
        return response
        
    except Exception as e:
        logger.error("Failed to get task status", error=str(e), task_id=task_id)
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.post("/demo", response_model=dict)
async def demo_audit(request: AuditStartRequest):
    """Demo audit that works without database - tests core scanning functionality"""
    try:
        logger.info("Starting demo audit", url=str(request.url))
        
        # Initialize audit service
        from app.services.audit_service import AuditService
        audit_service = AuditService()
        
        # Run basic analysis without database
        from app.services.security_scanner import SecurityScanner
        from app.services.performance_scanner import PerformanceScanner
        from app.services.ai_analyzer import AIAnalyzer
        
        security_scanner = SecurityScanner()
        performance_scanner = PerformanceScanner()
        ai_analyzer = AIAnalyzer()
        
        # Run scans
        security_results = await security_scanner.scan_website(str(request.url))
        performance_results = await performance_scanner.scan_website(str(request.url))
        
        # Basic SEO analysis
        seo_results = await audit_service._basic_seo_analysis(str(request.url))
        
        # Combine results
        audit_results = {
            "security": security_results,
            "performance": performance_results,
            "seo": seo_results
        }
        
        # Calculate scores
        scores = audit_service._calculate_scores(audit_results)
        
        # Generate AI summary
        ai_summary = await ai_analyzer.generate_summary(str(request.url), audit_results, scores)
        
        logger.info("Demo audit completed", url=str(request.url), overall_score=scores["overall"])
        
        return {
            "status": "completed",
            "url": str(request.url),
            "message": "Demo audit completed successfully",
            "scores": scores,
            "results": audit_results,
            "ai_summary": ai_summary,
            "note": "This is a demo audit that works without database. For full functionality, configure Supabase database."
        }
        
    except Exception as e:
        logger.error("Demo audit failed", error=str(e), url=str(request.url))
        raise HTTPException(status_code=500, detail=f"Demo audit failed: {str(e)}")


@router.get("/status/{audit_id}", response_model=AuditStatusResponse)
async def get_audit_status(
    audit_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get audit status"""
    try:
        # Query audit request
        stmt = select(AuditRequest).where(AuditRequest.id == uuid.UUID(audit_id))
        result = await db.execute(stmt)
        audit_request = result.scalar_one_or_none()
        
        if not audit_request:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        return AuditStatusResponse(
            id=str(audit_request.id),
            url=audit_request.url,
            status=audit_request.status,
            created_at=audit_request.created_at,
            updated_at=audit_request.updated_at,
            completed_at=audit_request.completed_at,
            processing_time=audit_request.processing_time,
            error_message=audit_request.error_message,
            overall_score=audit_request.overall_score,
            security_score=audit_request.security_score,
            performance_score=audit_request.performance_score,
            seo_score=audit_request.seo_score,
            ux_score=audit_request.ux_score,
            accessibility_score=audit_request.accessibility_score
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid audit ID format")
    except Exception as e:
        logger.error("Failed to get audit status", error=str(e), audit_id=audit_id)
        raise HTTPException(status_code=500, detail="Failed to get audit status")


@router.get("/results/{audit_id}", response_model=AuditResultResponse)
async def get_audit_results(
    audit_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get full audit results"""
    try:
        # Query audit request
        stmt = select(AuditRequest).where(AuditRequest.id == uuid.UUID(audit_id))
        result = await db.execute(stmt)
        audit_request = result.scalar_one_or_none()
        
        if not audit_request:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        if audit_request.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Audit not completed. Current status: {audit_request.status}"
            )
        
        return AuditResultResponse(
            id=str(audit_request.id),
            url=audit_request.url,
            status=audit_request.status,
            created_at=audit_request.created_at,
            completed_at=audit_request.completed_at,
            processing_time=audit_request.processing_time,
            overall_score=audit_request.overall_score,
            security_score=audit_request.security_score,
            performance_score=audit_request.performance_score,
            seo_score=audit_request.seo_score,
            ux_score=audit_request.ux_score,
            accessibility_score=audit_request.accessibility_score,
            results=audit_request.results,
            ai_summary=audit_request.ai_summary
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid audit ID format")
    except Exception as e:
        logger.error("Failed to get audit results", error=str(e), audit_id=audit_id)
        raise HTTPException(status_code=500, detail="Failed to get audit results")


async def process_audit_background(audit_id: str, url: str):
    """Background task to process audit"""
    try:
        logger.info("Starting audit processing", audit_id=audit_id, url=url)
        
        # Initialize audit service
        audit_service = AuditService()
        
        # Process the audit
        await audit_service.process_audit(audit_id, url)
        
        logger.info("Audit processing completed", audit_id=audit_id)
        
    except Exception as e:
        logger.error("Audit processing failed", error=str(e), audit_id=audit_id)
        
        # Update audit status to failed
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            stmt = select(AuditRequest).where(AuditRequest.id == uuid.UUID(audit_id))
            result = await db.execute(stmt)
            audit_request = result.scalar_one_or_none()
            
            if audit_request:
                audit_request.status = "failed"
                audit_request.error_message = str(e)
                audit_request.updated_at = datetime.utcnow()
                await db.commit()