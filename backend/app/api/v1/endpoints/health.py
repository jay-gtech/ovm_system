from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
import redis.asyncio as redis
from app.core.config import settings

router = APIRouter()

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    # DB Check
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Redis Check
    redis_status = "ok"
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "active",
        "database": db_status,
        "redis": redis_status,
        "version": settings.VERSION
    }
