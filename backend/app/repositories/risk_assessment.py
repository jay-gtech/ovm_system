import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import require_tenant_id
from app.db.tenancy import apply_tenant_scope
from app.models.risk_assessment import RiskAssessment, RiskLevel


class RiskAssessmentRepository:
    """
    Risk assessment data-access layer.

    All multi-record methods use apply_tenant_scope for isolation.
    find_recent() and get_latest_for_entity() use explicit organization_id
    so they are safe to call from background scanner jobs without an active
    request-scoped tenant ContextVar.
    """

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[RiskAssessment]:
        query = select(RiskAssessment).where(RiskAssessment.id == id)
        query = apply_tenant_scope(query, RiskAssessment)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        risk_level: Optional[str] = None,
        generated_after: Optional[datetime] = None,
        generated_before: Optional[datetime] = None,
        latest_only: bool = False,
    ) -> Sequence[RiskAssessment]:
        if latest_only:
            return await self.get_latest_per_entity(
                db,
                skip=skip,
                limit=limit,
                entity_type=entity_type,
                risk_level=risk_level,
            )

        query = select(RiskAssessment)
        query = apply_tenant_scope(query, RiskAssessment)
        query = self._apply_filters(
            query,
            entity_type=entity_type,
            entity_id=entity_id,
            risk_level=risk_level,
            generated_after=generated_after,
            generated_before=generated_before,
        )
        query = query.order_by(RiskAssessment.generated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        risk_level: Optional[str] = None,
        generated_after: Optional[datetime] = None,
        generated_before: Optional[datetime] = None,
        latest_only: bool = False,
    ) -> int:
        if latest_only:
            # Count via the latest-per-entity subquery (no limit applied).
            tenant_id = require_tenant_id()
            max_subq = self._max_per_entity_subq(tenant_id)
            query = (
                select(func.count(RiskAssessment.id))
                .join(
                    max_subq,
                    and_(
                        RiskAssessment.entity_type == max_subq.c.et,
                        RiskAssessment.entity_id == max_subq.c.eid,
                        RiskAssessment.generated_at == max_subq.c.max_gen,
                    ),
                )
                .where(RiskAssessment.organization_id == tenant_id)
            )
            if entity_type:
                query = query.where(RiskAssessment.entity_type == entity_type)
            if risk_level:
                query = query.where(RiskAssessment.risk_level == risk_level)
            result = await db.execute(query)
            return result.scalar_one()

        query = select(func.count(RiskAssessment.id))
        query = apply_tenant_scope(query, RiskAssessment)
        query = self._apply_filters(
            query,
            entity_type=entity_type,
            entity_id=entity_id,
            risk_level=risk_level,
            generated_after=generated_after,
            generated_before=generated_before,
        )
        result = await db.execute(query)
        return result.scalar_one()

    async def get_entity_history(
        self,
        db: AsyncSession,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        limit: int = 30,
    ) -> Sequence[RiskAssessment]:
        """Historical assessments for one entity, oldest-first (for trend chart)."""
        query = (
            select(RiskAssessment)
            .where(
                RiskAssessment.entity_type == entity_type,
                RiskAssessment.entity_id == entity_id,
            )
            .order_by(RiskAssessment.generated_at.asc())
            .limit(limit)
        )
        query = apply_tenant_scope(query, RiskAssessment)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_latest_per_entity(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        entity_type: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> Sequence[RiskAssessment]:
        """
        Return one (latest) assessment per entity for the current tenant.

        Uses a correlated max-per-entity subquery — returns only the most recent
        score per (entity_type, entity_id) pair, not all historical records.
        Used by the dashboard latest-only mode and summary overview.
        """
        tenant_id = require_tenant_id()
        max_subq = self._max_per_entity_subq(tenant_id)

        query = (
            select(RiskAssessment)
            .join(
                max_subq,
                and_(
                    RiskAssessment.entity_type == max_subq.c.et,
                    RiskAssessment.entity_id == max_subq.c.eid,
                    RiskAssessment.generated_at == max_subq.c.max_gen,
                ),
            )
            .where(RiskAssessment.organization_id == tenant_id)
        )
        if entity_type:
            query = query.where(RiskAssessment.entity_type == entity_type)
        if risk_level:
            query = query.where(RiskAssessment.risk_level == risk_level)

        query = query.order_by(RiskAssessment.generated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_risk_summary(self, db: AsyncSession) -> Dict[str, int]:
        """
        Count entities at each risk level based on their LATEST assessment.

        Single-query approach: join to max-per-entity subquery then group by risk_level.
        Returns {LOW: N, MEDIUM: N, HIGH: N, CRITICAL: N}.
        """
        tenant_id = require_tenant_id()
        max_subq = self._max_per_entity_subq(tenant_id)

        count_q = (
            select(
                RiskAssessment.risk_level,
                func.count(RiskAssessment.id).label("cnt"),
            )
            .join(
                max_subq,
                and_(
                    RiskAssessment.entity_type == max_subq.c.et,
                    RiskAssessment.entity_id == max_subq.c.eid,
                    RiskAssessment.generated_at == max_subq.c.max_gen,
                ),
            )
            .where(RiskAssessment.organization_id == tenant_id)
            .group_by(RiskAssessment.risk_level)
        )

        result = await db.execute(count_q)
        rows = result.all()

        counts: Dict[str, int] = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.CRITICAL: 0,
        }
        for row in rows:
            if row.risk_level in counts:
                counts[row.risk_level] = int(row.cnt)
        return counts

    async def get_latest_for_entity(
        self,
        db: AsyncSession,
        *,
        organization_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> Optional[RiskAssessment]:
        """
        Return the single most recent assessment for this entity (no time restriction).

        Uses explicit organization_id — safe for background-job callers.
        """
        query = (
            select(RiskAssessment)
            .where(
                RiskAssessment.organization_id == organization_id,
                RiskAssessment.entity_type == entity_type,
                RiskAssessment.entity_id == entity_id,
            )
            .order_by(RiskAssessment.generated_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def find_recent(
        self,
        db: AsyncSession,
        *,
        organization_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        within_minutes: int,
    ) -> Optional[RiskAssessment]:
        """
        Dedup gate: return a recent assessment if one was created within
        `within_minutes` minutes for this entity — prevents scanner spam.

        Uses explicit organization_id — safe for background-job callers.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
        query = (
            select(RiskAssessment)
            .where(
                RiskAssessment.organization_id == organization_id,
                RiskAssessment.entity_type == entity_type,
                RiskAssessment.entity_id == entity_id,
                RiskAssessment.generated_at >= cutoff,
            )
            .order_by(RiskAssessment.generated_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> RiskAssessment:
        assessment = RiskAssessment(**obj_in)
        db.add(assessment)
        await db.flush()
        await db.refresh(assessment)
        return assessment

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _max_per_entity_subq(tenant_id: uuid.UUID):
        """Subquery: max generated_at per (entity_type, entity_id) for one tenant."""
        return (
            select(
                RiskAssessment.entity_type.label("et"),
                RiskAssessment.entity_id.label("eid"),
                func.max(RiskAssessment.generated_at).label("max_gen"),
            )
            .where(RiskAssessment.organization_id == tenant_id)
            .group_by(RiskAssessment.entity_type, RiskAssessment.entity_id)
            .subquery()
        )

    @staticmethod
    def _apply_filters(
        query,
        *,
        entity_type: Optional[str],
        entity_id: Optional[uuid.UUID],
        risk_level: Optional[str],
        generated_after: Optional[datetime],
        generated_before: Optional[datetime],
    ):
        if entity_type:
            query = query.where(RiskAssessment.entity_type == entity_type)
        if entity_id:
            query = query.where(RiskAssessment.entity_id == entity_id)
        if risk_level:
            query = query.where(RiskAssessment.risk_level == risk_level)
        if generated_after:
            query = query.where(RiskAssessment.generated_at >= generated_after)
        if generated_before:
            query = query.where(RiskAssessment.generated_at <= generated_before)
        return query
