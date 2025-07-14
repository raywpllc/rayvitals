"""
User and site management models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class SiteRegistration(Base):
    """Site registration and authentication model"""
    __tablename__ = "site_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_url = Column(String(2048), nullable=False)
    site_token = Column(String(255), unique=True, nullable=False)
    
    # WordPress integration
    wp_user_id = Column(String(255), nullable=True)
    wp_site_url = Column(String(2048), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Configuration
    settings = Column(JSON, nullable=True)
    
    # Usage tracking
    total_scans = Column(Integer, default=0)
    monthly_scans = Column(Integer, default=0)
    last_scan_reset = Column(DateTime, nullable=True)


class ApiKey(Base):
    """API key management for external integrations"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_name = Column(String(255), nullable=False)
    api_key = Column(String(512), nullable=False)
    
    # Associated site
    site_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Permissions
    permissions = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Usage limits
    rate_limit = Column(Integer, default=60)  # requests per minute
    monthly_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)