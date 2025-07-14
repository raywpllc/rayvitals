"""
Database configuration and connection management
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
import structlog
# from supabase import create_client, Client

from app.core.config import settings

logger = structlog.get_logger()

# SQLAlchemy Base
Base = declarative_base()

# Async database engine (created on demand)
engine = None

def get_engine():
    global engine
    if engine is None and settings.DATABASE_URL:
        try:
            engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                future=True,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"server_settings": {"jit": "off"}}
            )
        except Exception as e:
            logger.error("Failed to create database engine", error=str(e))
    return engine

# Async session factory (created on demand)
async_session_factory = None

def get_session_factory():
    global async_session_factory
    if async_session_factory is None:
        engine = get_engine()
        if engine:
            async_session_factory = async_sessionmaker(
                engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
    return async_session_factory

# Supabase client (disabled for now due to version conflicts)
supabase_client = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    session_factory = get_session_factory()
    if not session_factory:
        raise RuntimeError("Database not configured - set DATABASE_URL environment variable")
    
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


def get_supabase_client():
    """Get Supabase client"""
    if not supabase_client:
        raise RuntimeError("Supabase client not available - using direct PostgreSQL connection")
    return supabase_client


async def init_db():
    """Initialize database tables"""
    engine = get_engine()
    if not engine:
        logger.warning("Database not configured - skipping initialization")
        return
        
    try:
        # Test the connection first
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            
            # Import models to ensure they're registered
            from app.models import audit, user
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        logger.warning("Continuing without database initialization - database features will be limited")
        # Don't raise the error, just log it and continue


async def close_db():
    """Close database connections"""
    engine = get_engine()
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")