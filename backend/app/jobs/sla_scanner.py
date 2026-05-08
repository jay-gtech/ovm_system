"""
SLA Evaluation Scanner Job
===========================
Scheduled every 15 minutes to evaluate unresolved alerts against SLA policies
and escalate/notify as required.

Design rules:
  - Per-org session isolation: one transaction per tenant; failures are logged
    and skipped so other orgs continue.
  - Tenant ContextVar: set_tenant_id / reset_tenant_id before service calls.
  - No N+1 queries: active users are fetched once per org per cycle.
  - Escalation deduplication: escalation_level on Alert prevents re-escalation.
  - Notification deduplication: NotificationService checks find_recent() before
    creating new records.
  - Scheduler safety: obeys the single-instance ENABLE_SCHEDULER flag.
"""

import logging
import uuid
from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import reset_tenant_id, set_tenant_id
from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.services.sla import SLAService

logger = logging.getLogger(__name__)


async def _get_active_org_ids() -> List[uuid.UUID]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Organization.id).where(Organization.is_active.is_(True))
        )
        return list(result.scalars().all())


async def _get_active_users_for_org(
    session: AsyncSession, org_id: uuid.UUID
) -> Sequence[User]:
    """
    Fetch all active, non-deleted users for the organization.

    These users receive escalation and SLA-breach notifications.
    Role-based targeting (ADMIN/MANAGER/ACCOUNTS only) can be added here
    once the RBAC system is fully wired — for now all active org members
    receive operational alerts.
    """
    result = await session.execute(
        select(User).where(
            User.organization_id == org_id,
            User.is_active.is_(True),
            User.is_deleted.is_(False),
        )
    )
    return result.scalars().all()


async def _evaluate_sla_for_org(session: AsyncSession, org_id: uuid.UUID) -> None:
    active_users = await _get_active_users_for_org(session, org_id)
    svc = SLAService(db=session)
    summary = await svc.evaluate_org(
        organization_id=org_id,
        active_users=active_users,
    )
    if summary["escalated"] > 0 or summary["breached"] > 0:
        logger.info(
            "SLA scan org=%s — escalated=%d breached=%d",
            org_id, summary["escalated"], summary["breached"],
        )


async def scan_sla_evaluations() -> None:
    """APScheduler job — runs every 15 minutes."""
    logger.info("Starting SLA evaluation scan")
    org_ids = await _get_active_org_ids()
    processed = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    await _evaluate_sla_for_org(session, org_id)
                    await session.commit()
                    processed += 1
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("SLA scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("SLA evaluation scan complete — %d orgs processed", processed)
