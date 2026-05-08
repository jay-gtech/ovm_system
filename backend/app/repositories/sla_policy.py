import uuid
from typing import Dict, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenancy import apply_tenant_scope
from app.models.sla_policy import SLAPolicy


class SLAPolicyRepository:

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[SLAPolicy]:
        query = select(SLAPolicy).where(SLAPolicy.id == id)
        query = apply_tenant_scope(query, SLAPolicy)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_for_org(
        self, db: AsyncSession, *, organization_id: uuid.UUID
    ) -> Sequence[SLAPolicy]:
        """Return all active SLA policies for an org keyed by alert_type."""
        query = select(SLAPolicy).where(
            SLAPolicy.organization_id == organization_id,
            SLAPolicy.is_active.is_(True),
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_map(
        self, db: AsyncSession, *, organization_id: uuid.UUID
    ) -> Dict[str, SLAPolicy]:
        """Return {alert_type: SLAPolicy} for quick per-alert lookup in scanner."""
        policies = await self.get_active_for_org(db, organization_id=organization_id)
        return {p.alert_type: p for p in policies}

    async def get_by_alert_type(
        self,
        db: AsyncSession,
        *,
        organization_id: uuid.UUID,
        alert_type: str,
    ) -> Optional[SLAPolicy]:
        query = select(SLAPolicy).where(
            SLAPolicy.organization_id == organization_id,
            SLAPolicy.alert_type == alert_type,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_for_tenant(self, db: AsyncSession) -> Sequence[SLAPolicy]:
        query = select(SLAPolicy)
        query = apply_tenant_scope(query, SLAPolicy)
        query = query.order_by(SLAPolicy.alert_type)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> SLAPolicy:
        policy = SLAPolicy(**obj_in)
        db.add(policy)
        await db.flush()
        await db.refresh(policy)
        return policy

    async def update(
        self, db: AsyncSession, *, db_obj: SLAPolicy, obj_in: dict
    ) -> SLAPolicy:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
