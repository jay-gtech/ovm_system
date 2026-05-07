from fastapi import APIRouter
from app.api.v1.endpoints import health, organizations, users, vendors

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
