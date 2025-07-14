"""
RayVitals Backend API - Main Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting RayVitals Backend API")
    
    # Initialize database
    await init_db()
    
    yield
    
    logger.info("Shutting down RayVitals Backend API")


# Create FastAPI application
app = FastAPI(
    title="RayVitals Backend API",
    description="AI-powered website intelligence platform backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RayVitals Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rayvitals-backend"}


@app.get("/test", response_class=HTMLResponse)
async def test_interface():
    """Serve the test interface"""
    try:
        with open("test_interface.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Test Interface Not Found</title></head>
        <body>
        <h1>Test Interface Not Found</h1>
        <p>The test_interface.html file was not found.</p>
        <p>Try accessing the API directly at:</p>
        <ul>
        <li><a href="/docs">API Documentation</a></li>
        <li><a href="/health">Health Check</a></li>
        </ul>
        </body>
        </html>
        """, status_code=404)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error("HTTP exception occurred", 
                status_code=exc.status_code, 
                detail=exc.detail,
                path=request.url.path)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unexpected error occurred", 
                error=str(exc),
                path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )