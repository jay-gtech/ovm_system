import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services.user import UserService
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
)
from app.models.user import User

router = APIRouter()
user_service = UserService()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new user.

    TODO(rbac): Upgrade to check_role(["admin"]) once RBAC is wired.
    Until then, any active tenant member can create users — must be locked
    down before staging.
    """
    try:
        return await user_service.create_user(uow, user_in=user_in)
    except ConflictDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    users = await user_service.list_users(uow, skip=skip, limit=limit)
    return {"items": users, "total": len(users)}


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user. Non-superusers may only update their own record.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    try:
        return await user_service.update_user(uow, user_id=user_id, user_in=user_in)
    except NotFoundDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
