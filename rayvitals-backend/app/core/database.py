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
            from urllib.parse import urlparse, parse_qs, urlunparse
            
            # Parse and convert PostgreSQL URL to asyncpg format
            database_url = settings.DATABASE_URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            
            # Parse URL to extract SSL parameters for asyncpg
            parsed = urlparse(database_url)
            query_params = parse_qs(parsed.query)
            
            # Extract SSL mode and remove from URL if present
            ssl_mode = None
            if 'sslmode' in query_params:
                ssl_mode = query_params['sslmode'][0]
                # Remove sslmode from query params
                del query_params['sslmode']
                
                # Rebuild URL without sslmode
                new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
                database_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
            
            # Configure connect_args for asyncpg
            connect_args = {"server_settings": {"jit": "off"}}
            
            # Add SSL configuration if needed - asyncpg uses different SSL parameter format
            if ssl_mode == 'require':
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connect_args['ssl'] = ssl_context
            elif ssl_mode == 'prefer':
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connect_args['ssl'] = ssl_context
            # For 'disable', don't add SSL to connect_args
            
            engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                future=True,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args=connect_args
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