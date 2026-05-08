import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification import NotificationService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

_ALLOWED_ROLES = ["ADMIN", "MANAGER", "ACCOUNTS"]


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = Query(default=None, description="PENDING | SENT | FAILED | READ"),
    notification_type: Optional[str] = Query(default=None),
    channel: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    List notifications for the currently authenticated user (tenant-scoped).

    Users only see their own notifications — user_id is always set from JWT.
    """
    repo = NotificationRepository()
    items = await repo.get_multi(
        db,
        user_id=current_user.id,
        status=status,
        notification_type=notification_type,
        channel=channel,
        skip=skip,
        limit=limit,
    )
    total = await repo.count(
        db,
        user_id=current_user.id,
        status=status,
        notification_type=notification_type,
        channel=channel,
    )
    return NotificationListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Return the count of unread (PENDING + SENT) notifications for the bell badge."""
    repo = NotificationRepository()
    count = await repo.count_unread_for_user(db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Mark a notification as READ.

    Returns 404 if not found in the current tenant.
    Returns 400 if the notification belongs to a different user.
    Idempotent — calling on an already-READ notification is a no-op.
    """
    svc = NotificationService(db=uow.session)
    try:
        notif = await svc.mark_read(
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await uow.commit()
    return notif
