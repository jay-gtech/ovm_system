import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.db.tenancy import apply_tenant_scope


class AuditRepository:
    """
    Read-only repository for querying the immutable audit log.

    All queries are automatically scoped to the active tenant via apply_tenant_scope().
    No write methods exist here — writes go through AuditService.log_event() directly.
    """

    async def get_by_entity(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[AuditLog]:
        """Return paginated audit entries for a specific entity, newest first."""
        query = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        query = apply_tenant_scope(query, AuditLog)
        result = await db.execute(query)
        return result.scalars().all()

    async def count_by_entity(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> int:
        """Return total count of audit entries for a specific entity."""
        query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
        )
        query = apply_tenant_scope(query, AuditLog)
        result = await db.execute(query)
        return result.scalar_one()

    async def search(
        self,
        db: AsyncSession,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[AuditLog]:
        """Search audit logs with optional filters, newest first."""
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        query = apply_tenant_scope(query, AuditLog)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if action:
            query = query.where(AuditLog.action == action)
        if actor_user_id:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                query = query.where(AuditLog.created_at >= dt)
            except ValueError:
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                query = query.where(AuditLog.created_at <= dt)
            except ValueError:
                pass

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def search_count(
        self,
        db: AsyncSession,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> int:
        """Return total count for a search query (mirrors search() filters without pagination)."""
        query = select(func.count()).select_from(AuditLog)
        query = apply_tenant_scope(query, AuditLog)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if action:
            query = query.where(AuditLog.action == action)
        if actor_user_id:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                query = query.where(AuditLog.created_at >= dt)
            except ValueError:
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                query = query.where(AuditLog.created_at <= dt)
            except ValueError:
                pass

        result = await db.execute(query)
        return result.scalar_one()
