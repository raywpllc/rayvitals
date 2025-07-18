"""
API v1 router configuration
"""

from fastapi import APIRouter

from .endpoints import audit, health, auth

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])