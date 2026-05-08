import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.tenant import TenantContextMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware stack — Starlette builds in LIFO (reverse-add) order, so the
# LAST middleware added becomes the OUTERMOST layer (runs first on requests).
#
# Add order (innermost → outermost):
#   1. TenantContextMiddleware   — extracts tenant/user from JWT
#   2. CorrelationIdMiddleware   — assigns X-Request-ID to ContextVar
#   3. CORSMiddleware            — outermost: intercepts OPTIONS pre-flight
#                                  before any BaseHTTPMiddleware runs
#
# Execution order (request → route handler):
#   CORSMiddleware → CorrelationIdMiddleware → TenantContextMiddleware → router
# ---------------------------------------------------------------------------

# TenantContextMiddleware is innermost: added first so it runs last before routes.
app.add_middleware(TenantContextMiddleware)

# CorrelationIdMiddleware wraps TenantContext so every request carries a
# traceable request_id when tenant extraction runs.
app.add_middleware(CorrelationIdMiddleware)

# CORSMiddleware is outermost: added last so it runs first on every request.
# This guarantees OPTIONS pre-flight responses are returned immediately —
# before any BaseHTTPMiddleware in the stack can interfere.
# Vite local development origins are explicitly listed alongside any origins
# declared in settings.ALLOWED_ORIGINS.
_all_origins = [str(o).rstrip("/") for o in settings.ALLOWED_ORIGINS]
_all_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(_all_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Lifespan events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("OVM System starting up — environment: %s", settings.ENVIRONMENT)
    if settings.ENABLE_SCHEDULER:
        from app.core.scheduler import scheduler, setup_scheduler
        setup_scheduler()
        scheduler.start()
        logger.info("Background alert scanner scheduler started (ENABLE_SCHEDULER=true).")
    else:
        logger.info(
            "Background scheduler DISABLED (ENABLE_SCHEDULER=false). "
            "Set ENABLE_SCHEDULER=true on exactly ONE primary worker to enable scans."
        )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("OVM System shutting down.")
    if settings.ENABLE_SCHEDULER:
        from app.core.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Background scheduler shut down.")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_V1_STR)
