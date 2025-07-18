"""
Authentication and API key management endpoints
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import structlog

from app.core.database import get_async_session
from app.core.security import SecurityManager, get_current_api_key
from app.models.user import ApiKey, SiteRegistration

logger = structlog.get_logger()

router = APIRouter()


class CreateApiKeyRequest(BaseModel):
    key_name: str
    site_url: Optional[str] = None
    rate_limit: Optional[int] = 60
    monthly_limit: Optional[int] = None
    expires_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: str
    key_name: str
    api_key: str  # Only returned on creation
    site_url: Optional[str] = None
    rate_limit: int
    monthly_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool


class ApiKeyInfo(BaseModel):
    id: str
    key_name: str
    site_url: Optional[str] = None
    rate_limit: int
    monthly_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int
    is_active: bool


@router.post("/create-key", response_model=ApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new API key for accessing the audit API
    
    Note: This endpoint is currently open for development.
    In production, this should be protected by admin authentication.
    """
    try:
        # Generate API key
        plain_key = SecurityManager.generate_api_key()
        hashed_key = SecurityManager.hash_api_key(plain_key)
        
        # Calculate expiry if specified
        expires_at = None
        if request.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
        
        # Create API key record
        api_key_record = ApiKey(
            key_name=request.key_name,
            api_key=hashed_key,
            rate_limit=request.rate_limit or 60,
            monthly_limit=request.monthly_limit,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(api_key_record)
        await db.commit()
        await db.refresh(api_key_record)
        
        logger.info("API key created", key_id=api_key_record.id, key_name=request.key_name)
        
        return ApiKeyResponse(
            id=str(api_key_record.id),
            key_name=api_key_record.key_name,
            api_key=plain_key,  # Return plain key only on creation
            site_url=request.site_url,
            rate_limit=api_key_record.rate_limit,
            monthly_limit=api_key_record.monthly_limit,
            expires_at=api_key_record.expires_at,
            created_at=api_key_record.created_at,
            is_active=api_key_record.is_active
        )
        
    except Exception as e:
        logger.error("Failed to create API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/keys", response_model=List[ApiKeyInfo])
async def list_api_keys(
    current_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_async_session)
):
    """
    List all API keys (requires valid API key)
    
    Note: In production, this should be restricted to admin keys only
    """
    try:
        result = await db.execute(select(ApiKey))
        api_keys = result.scalars().all()
        
        return [
            ApiKeyInfo(
                id=str(key.id),
                key_name=key.key_name,
                site_url=None,  # TODO: Get from site registration
                rate_limit=key.rate_limit,
                monthly_limit=key.monthly_limit,
                expires_at=key.expires_at,
                created_at=key.created_at,
                last_used=key.last_used,
                usage_count=key.usage_count,
                is_active=key.is_active
            )
            for key in api_keys
        ]
        
    except Exception as e:
        logger.error("Failed to list API keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete (deactivate) an API key
    """
    try:
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.is_active = False
        await db.commit()
        
        logger.info("API key deactivated", key_id=key_id)
        
        return {"message": "API key deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete API key", error=str(e), key_id=key_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.get("/validate")
async def validate_api_key(
    current_key: ApiKey = Depends(get_current_api_key)
):
    """
    Validate the current API key and return info
    """
    return {
        "valid": True,
        "key_name": current_key.key_name,
        "rate_limit": current_key.rate_limit,
        "monthly_limit": current_key.monthly_limit,
        "usage_count": current_key.usage_count,
        "expires_at": current_key.expires_at,
        "last_used": current_key.last_used
    }