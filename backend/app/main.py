import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.middleware.correlation import CorrelationIdMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware stack — Starlette executes middleware in LIFO (reverse-add) order.
# Add outermost layers last so they wrap all inner layers.
#
# Execution order (request in → response out):
#   1. CORSMiddleware       — handles OPTIONS pre-flight first
#   2. CorrelationIdMiddleware — assigns X-Request-ID before any handler runs
# ---------------------------------------------------------------------------

# CORS must be outermost so pre-flight OPTIONS responses are returned
# immediately without passing through the correlation middleware.
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# CorrelationIdMiddleware runs inside CORS so every non-OPTIONS request
# gets a traceable request_id bound to its ContextVar before hitting routes.
app.add_middleware(CorrelationIdMiddleware)


# ---------------------------------------------------------------------------
# Lifespan events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("OVM System starting up — environment: %s", settings.ENVIRONMENT)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("OVM System shutting down.")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_V1_STR)
