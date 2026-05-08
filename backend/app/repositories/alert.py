import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenancy import apply_tenant_scope
from app.models.alert import Alert, AlertStatus


class AlertRepository:
    """
    Alert data-access layer.

    All methods that list/get alerts use apply_tenant_scope() and therefore
    require the tenant ContextVar to be set (set by middleware in request
    context, or explicitly by the scanner in background context).

    find_active() uses an explicit organization_id parameter and bypasses
    apply_tenant_scope — safe for both request and background-job callers.
    """

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Alert]:
        query = select(Alert).where(Alert.id == id)
        query = apply_tenant_scope(query, Alert)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        triggered_after: Optional[datetime] = None,
        triggered_before: Optional[datetime] = None,
    ) -> Sequence[Alert]:
        query = select(Alert)
        query = apply_tenant_scope(query, Alert)
        query = self._apply_filters(
            query, status=status, severity=severity, alert_type=alert_type,
            entity_type=entity_type, entity_id=entity_id,
            triggered_after=triggered_after, triggered_before=triggered_before,
        )
        query = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        triggered_after: Optional[datetime] = None,
        triggered_before: Optional[datetime] = None,
    ) -> int:
        query = select(func.count(Alert.id))
        query = apply_tenant_scope(query, Alert)
        query = self._apply_filters(
            query, status=status, severity=severity, alert_type=alert_type,
            entity_type=entity_type, entity_id=entity_id,
            triggered_after=triggered_after, triggered_before=triggered_before,
        )
        result = await db.execute(query)
        return result.scalar_one()

    async def find_active(
        self,
        db: AsyncSession,
        *,
        organization_id: uuid.UUID,
        alert_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> Optional[Alert]:
        """
        Deduplication gate: returns an existing OPEN or ACKNOWLEDGED alert for
        the same (tenant, type, entity) combination, or None if no active alert exists.

        Uses explicit organization_id rather than apply_tenant_scope so it works
        safely from both request context and background scanner jobs.
        """
        query = select(Alert).where(
            Alert.organization_id == organization_id,
            Alert.alert_type == alert_type,
            Alert.entity_type == entity_type,
            Alert.entity_id == entity_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> Alert:
        alert = Alert(**obj_in)
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert

    async def update(self, db: AsyncSession, *, db_obj: Alert, obj_in: dict) -> Alert:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(query, *, status, severity, alert_type, entity_type,
                       entity_id, triggered_after, triggered_before):
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)
        if alert_type:
            query = query.where(Alert.alert_type == alert_type)
        if entity_type:
            query = query.where(Alert.entity_type == entity_type)
        if entity_id:
            query = query.where(Alert.entity_id == entity_id)
        if triggered_after:
            query = query.where(Alert.triggered_at >= triggered_after)
        if triggered_before:
            query = query.where(Alert.triggered_at <= triggered_before)
        return query
