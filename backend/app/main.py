from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
import structlog

# Setup logging
structlog.configure()
logger = structlog.get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up OVM System...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down OVM System...")
