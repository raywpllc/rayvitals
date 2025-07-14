#!/usr/bin/env python3
"""
Test database connection from host system
"""
import asyncio
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
from app.core.database import init_db, engine
from app.core.config import settings

async def test_db_connection():
    """Test database connection and initialization"""
    print("=== RayVitals Database Connection Test ===")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    if not engine:
        print("❌ Database engine not initialized - check DATABASE_URL")
        return False
    
    try:
        print("🔄 Testing database connection...")
        await init_db()
        print("✅ Database connection successful!")
        print("✅ Database tables created/verified!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    success = asyncio.run(test_db_connection())
    if success:
        print("\n🎉 Database is ready for use!")
    else:
        print("\n⚠️  Database connection failed - API will run with limited functionality")