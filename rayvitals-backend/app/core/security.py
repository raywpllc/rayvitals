"""
Security utilities for API authentication and authorization
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_async_session
from app.models.user import ApiKey

logger = structlog.get_logger()

security = HTTPBearer()


class SecurityManager:
    """Handles API key generation, validation, and security operations"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        # Generate a 32-byte random key and encode as hex
        raw_key = secrets.token_bytes(32)
        return f"rv_{raw_key.hex()}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash"""
        return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_async_session)
) -> ApiKey:
    """
    Validate API key and return the associated ApiKey record
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    # Validate API key format
    if not api_key.startswith("rv_") or len(api_key) != 67:  # rv_ + 64 hex chars
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hash the provided key to compare with stored hash
    hashed_key = SecurityManager.hash_api_key(api_key)
    
    # Look up the API key in the database
    try:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.api_key == hashed_key,
                ApiKey.is_active == True
            )
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record:
            logger.warning("Invalid API key attempted", key_prefix=api_key[:10])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if key is expired
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            logger.warning("Expired API key attempted", key_id=api_key_record.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last used timestamp
        api_key_record.last_used = datetime.utcnow()
        api_key_record.usage_count += 1
        await db.commit()
        
        logger.info("API key validated", key_id=api_key_record.id, key_name=api_key_record.key_name)
        return api_key_record
        
    except Exception as e:
        logger.error("Database error during API key validation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def check_rate_limit(
    api_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_async_session)
) -> ApiKey:
    """
    Check rate limiting for the API key
    """
    # For now, we'll implement basic rate limiting
    # In a production system, you'd want to use Redis for this
    
    # Check monthly limits
    if api_key.monthly_limit:
        # Reset monthly counter if needed (simplified logic)
        now = datetime.utcnow()
        if (not api_key.last_scan_reset or 
            (now - api_key.last_scan_reset).days >= 30):
            api_key.usage_count = 0
            api_key.last_scan_reset = now
            await db.commit()
        
        if api_key.usage_count >= api_key.monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly limit of {api_key.monthly_limit} requests exceeded"
            )
    
    return api_key


def get_optional_api_key():
    """
    Optional API key dependency for endpoints that can work with or without auth
    """
    async def _get_optional_api_key(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False),
        db: AsyncSession = Depends(get_async_session)
    ) -> Optional[ApiKey]:
        if not credentials:
            return None
        
        try:
            # Use the same validation logic but don't raise errors
            return await get_current_api_key(credentials, db)
        except HTTPException:
            return None
    
    return _get_optional_api_key


class RateLimiter:
    """Simple in-memory rate limiter (for production, use Redis)"""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                req_time for req_time in self._requests[key] 
                if req_time > window_start
            ]
        else:
            self._requests[key] = []
        
        # Check if under limit
        if len(self._requests[key]) >= limit:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()