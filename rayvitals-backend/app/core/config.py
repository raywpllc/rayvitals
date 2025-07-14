"""
Configuration settings for RayVitals Backend API
"""

from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = False
    APP_NAME: str = "RayVitals Backend API"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = os.urandom(32).hex()
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Database - Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    DATABASE_URL: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # AI - Google Gemini
    GEMINI_API_KEY: str = ""
    
    # External APIs
    PAGESPEED_API_KEY: str = ""
    SSL_LABS_API_URL: str = "https://api.ssllabs.com/api/v3"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Job processing
    MAX_AUDIT_DURATION: int = 300  # 5 minutes
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()