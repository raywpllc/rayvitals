#!/usr/bin/env python3
"""
Create an initial API key for the RayVitals API
"""

import asyncio
import sys
from app.core.database import get_async_session, init_db
from app.core.security import SecurityManager
from app.models.user import ApiKey


async def create_initial_api_key():
    """Create an initial API key for WordPress plugin development"""
    print("Initializing database...")
    await init_db()
    
    async for session in get_async_session():
        try:
            # Generate API key
            plain_key = SecurityManager.generate_api_key()
            hashed_key = SecurityManager.hash_api_key(plain_key)
            
            # Create API key record
            api_key_record = ApiKey(
                key_name="WordPress Plugin Development",
                api_key=hashed_key,
                rate_limit=120,  # Higher limit for development
                monthly_limit=10000,  # 10k requests per month
                is_active=True
            )
            
            session.add(api_key_record)
            await session.commit()
            await session.refresh(api_key_record)
            
            print(f"✅ API Key created successfully!")
            print(f"")
            print(f"🔑 API Key: {plain_key}")
            print(f"📛 Key Name: {api_key_record.key_name}")
            print(f"🆔 Key ID: {api_key_record.id}")
            print(f"⚡ Rate Limit: {api_key_record.rate_limit} requests/minute")
            print(f"📊 Monthly Limit: {api_key_record.monthly_limit:,} requests/month")
            print(f"")
            print(f"⚠️  IMPORTANT: Save this API key securely - it won't be shown again!")
            print(f"")
            print(f"🔌 WordPress Plugin Configuration:")
            print(f"   API URL: https://rayvitals-backend-xwq86.ondigitalocean.app")
            print(f"   API Key: {plain_key}")
            print(f"")
            
            return plain_key
            
        except Exception as e:
            print(f"❌ Failed to create API key: {e}")
            return None


if __name__ == "__main__":
    asyncio.run(create_initial_api_key())