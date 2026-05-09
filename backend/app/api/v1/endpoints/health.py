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

    # Scheduler Check
    scheduler_status = "disabled"
    active_jobs = 0
    if settings.ENABLE_SCHEDULER:
        from app.core.scheduler import scheduler
        scheduler_status = "running" if scheduler.running else "stopped"
        active_jobs = len(scheduler.get_jobs()) if scheduler.running else 0

    return {
        "status": "active",
        "database": db_status,
        "redis": redis_status,
        "version": settings.VERSION,
        "scheduler": {
            "status": scheduler_status,
            "active_jobs": active_jobs,
        },
        "ocr": {
            "status": "ok" if settings.OCR_SERVICE_URL else "mocked",
        },
        "storage": {
            "status": "ok" if settings.S3_BUCKET else "local",
        },
        "queue_backlog": 0, # Placeholder for fast return
        "migration_status": "ok", # Can be extended to query alembic_version
    }
