import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis.asyncio as redis
import os

# Manual config for validation
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/ovm_db"
REDIS_URL = "redis://localhost:6379/0"

async def validate():
    print("Testing connections...")
    
    # DB Test
    try:
        engine = create_async_engine(DB_URL)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database: Connected (PostgreSQL 16)")
    except Exception as e:
        print(f"❌ Database: Failed - {e}")

    # Redis Test
    try:
        r = redis.from_url(REDIS_URL)
        await r.ping()
        print("✅ Redis: Connected (Redis 7)")
        await r.close()
    except Exception as e:
        print(f"❌ Redis: Failed - {e}")

if __name__ == "__main__":
    asyncio.run(validate())
