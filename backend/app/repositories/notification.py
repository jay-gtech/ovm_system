import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenancy import apply_tenant_scope
from app.models.notification import Notification, NotificationStatus


class NotificationRepository:

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Notification]:
        query = select(Notification).where(Notification.id == id)
        query = apply_tenant_scope(query, Notification)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        channel: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Notification]:
        query = select(Notification)
        query = apply_tenant_scope(query, Notification)
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if status:
            query = query.where(Notification.status == status)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if channel:
            query = query.where(Notification.channel == channel)
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> int:
        query = select(func.count(Notification.id))
        query = apply_tenant_scope(query, Notification)
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if status:
            query = query.where(Notification.status == status)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if channel:
            query = query.where(Notification.channel == channel)
        result = await db.execute(query)
        return result.scalar_one()

    async def count_unread_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> int:
        """Fast lookup for the notification bell badge count."""
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SENT]),
        )
        query = apply_tenant_scope(query, Notification)
        result = await db.execute(query)
        return result.scalar_one()

    async def find_recent(
        self,
        db: AsyncSession,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        notification_type: str,
        related_entity_id: uuid.UUID,
        since: datetime,
    ) -> Optional[Notification]:
        """
        Deduplication guard: return an existing notification of the same type for
        the same entity + user created after *since*, or None.

        Uses explicit organization_id to work safely from background job context.
        """
        query = select(Notification).where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.notification_type == notification_type,
            Notification.related_entity_id == related_entity_id,
            Notification.created_at >= since,
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> Notification:
        notif = Notification(**obj_in)
        db.add(notif)
        await db.flush()
        await db.refresh(notif)
        return notif

    async def update(
        self, db: AsyncSession, *, db_obj: Notification, obj_in: dict
    ) -> Notification:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
