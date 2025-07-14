"""
Audit data models
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class AuditRequest(Base):
    """Audit request model"""
    __tablename__ = "audit_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # User/site identification
    site_token = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Results
    results = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    
    # Scoring
    overall_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    seo_score = Column(Float, nullable=True)
    ux_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)


class AuditResult(Base):
    """Detailed audit results model"""
    __tablename__ = "audit_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), nullable=False)
    category = Column(String(100), nullable=False)  # security, performance, seo, ux, accessibility
    
    # Raw data
    raw_data = Column(JSON, nullable=True)
    
    # Processed results
    score = Column(Float, nullable=True)
    issues = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float, nullable=True)
    
    # AI Analysis
    ai_analysis = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)


class AuditMetrics(Base):
    """Audit metrics and performance data"""
    __tablename__ = "audit_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Performance metrics
    page_load_time = Column(Float, nullable=True)
    first_contentful_paint = Column(Float, nullable=True)
    largest_contentful_paint = Column(Float, nullable=True)
    first_input_delay = Column(Float, nullable=True)
    cumulative_layout_shift = Column(Float, nullable=True)
    
    # Security metrics
    ssl_score = Column(Float, nullable=True)
    security_headers_score = Column(Float, nullable=True)
    
    # SEO metrics
    mobile_friendly = Column(Boolean, nullable=True)
    page_speed_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)