"""
SLA Evaluation Engine
=====================
Evaluates unresolved alerts against their configured SLA policy and:
  1. Escalates the escalation_level field (0 → 1 → 2).
  2. Stamps sla_breached_at when the resolution window expires.
  3. Creates IN_APP notifications for the org's active users.

Escalation flow (no downgrade):
    Level 0 → Level 1  when (now - triggered_at) >= escalation_level_1_minutes
    Level 1 → Level 2  when (now - triggered_at) >= escalation_level_2_minutes
    Any level          → sla_breached_at stamped when (now - triggered_at)
                         >= resolution_minutes AND alert not yet RESOLVED

Transaction contract: callers (scanner jobs) commit after each org scan.

Audit: every escalation and SLA breach is written to AuditLog.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.models.audit_log import AuditAction
from app.models.notification import NotificationType
from app.models.sla_policy import SLAPolicy
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.sla_policy import SLAPolicyRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class SLAService:
    """
    Centralized SLA evaluation, escalation, and breach-marking engine.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._alert_repo = AlertRepository()
        self._policy_repo = SLAPolicyRepository()

    # ------------------------------------------------------------------
    # Main entry — called per-org by the scheduler job
    # ------------------------------------------------------------------

    async def evaluate_org(
        self,
        *,
        organization_id: uuid.UUID,
        active_users: Sequence[User],
    ) -> Dict[str, int]:
        """
        Run a full SLA evaluation pass for one organization.

        Returns a summary dict: {'escalated': N, 'breached': N}.
        """
        policy_map = await self._policy_repo.get_active_map(
            self.db, organization_id=organization_id
        )
        if not policy_map:
            return {"escalated": 0, "breached": 0}

        # Fetch OPEN/ACKNOWLEDGED alerts only for types that have an SLA policy.
        alert_types = list(policy_map.keys())
        query = select(Alert).where(
            Alert.organization_id == organization_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            Alert.alert_type.in_(alert_types),
        )
        result = await self.db.execute(query)
        alerts = result.scalars().all()

        now = datetime.now(timezone.utc)
        escalated_count = 0
        breached_count = 0

        for alert in alerts:
            policy = policy_map.get(alert.alert_type)
            if policy is None:
                continue

            elapsed_minutes = (now - alert.triggered_at).total_seconds() / 60

            # SLA breach check (independent of escalation level)
            if (
                alert.sla_breached_at is None
                and elapsed_minutes >= policy.resolution_minutes
            ):
                await self.mark_sla_breach(alert=alert, now=now)
                await self._notify_users(
                    organization_id=organization_id,
                    active_users=active_users,
                    notification_type=NotificationType.SLA_BREACHED,
                    title=f"SLA Breached: {alert.title}",
                    message=(
                        f"Alert '{alert.title}' has exceeded the "
                        f"{policy.resolution_minutes}-minute resolution SLA."
                    ),
                    related_entity_type="alert",
                    related_entity_id=alert.id,
                )
                breached_count += 1

            # Escalation level 2
            if (
                alert.escalation_level < 2
                and elapsed_minutes >= policy.escalation_level_2_minutes
            ):
                await self.escalate_alert(alert=alert, new_level=2, now=now)
                await self._notify_users(
                    organization_id=organization_id,
                    active_users=active_users,
                    notification_type=NotificationType.ALERT_ESCALATED,
                    title=f"[CRITICAL] Escalated to Level 2: {alert.title}",
                    message=(
                        f"Alert '{alert.title}' has been escalated to critical level 2 "
                        f"after {int(elapsed_minutes)} minutes without resolution."
                    ),
                    related_entity_type="alert",
                    related_entity_id=alert.id,
                )
                escalated_count += 1

            # Escalation level 1 (only if not already at level 1+)
            elif (
                alert.escalation_level < 1
                and elapsed_minutes >= policy.escalation_level_1_minutes
            ):
                await self.escalate_alert(alert=alert, new_level=1, now=now)
                await self._notify_users(
                    organization_id=organization_id,
                    active_users=active_users,
                    notification_type=NotificationType.ALERT_ESCALATED,
                    title=f"[HIGH] Escalated to Level 1: {alert.title}",
                    message=(
                        f"Alert '{alert.title}' has been escalated after "
                        f"{int(elapsed_minutes)} minutes without acknowledgement."
                    ),
                    related_entity_type="alert",
                    related_entity_id=alert.id,
                )
                escalated_count += 1

        logger.info(
            "SLA evaluation complete: org=%s escalated=%d breached=%d",
            organization_id, escalated_count, breached_count,
        )
        return {"escalated": escalated_count, "breached": breached_count}

    # ------------------------------------------------------------------
    # Atomic state mutations — no commit inside; caller commits
    # ------------------------------------------------------------------

    async def escalate_alert(
        self,
        *,
        alert: Alert,
        new_level: int,
        now: Optional[datetime] = None,
    ) -> Alert:
        """
        Increment escalation_level to new_level (no downgrade enforced).
        Stamps escalated_at on the first escalation.
        """
        if new_level <= alert.escalation_level:
            return alert  # already at or above requested level

        now = now or datetime.now(timezone.utc)
        old_level = alert.escalation_level
        update = {"escalation_level": new_level}
        if alert.escalated_at is None:
            update["escalated_at"] = now

        for field, value in update.items():
            setattr(alert, field, value)
        self.db.add(alert)
        await self.db.flush()

        await AuditService.log_event(
            self.db,
            entity_type="alert",
            entity_id=alert.id,
            action=AuditAction.ALERT_ESCALATED,
            field_name="escalation_level",
            old_value=old_level,
            new_value=new_level,
        )
        logger.info(
            "Alert %s escalated: level %d → %d", alert.id, old_level, new_level
        )
        return alert

    async def mark_sla_breach(
        self,
        *,
        alert: Alert,
        now: Optional[datetime] = None,
    ) -> Alert:
        """
        Stamp sla_breached_at once — idempotent if already set.
        """
        if alert.sla_breached_at is not None:
            return alert

        now = now or datetime.now(timezone.utc)
        alert.sla_breached_at = now
        self.db.add(alert)
        await self.db.flush()

        await AuditService.log_event(
            self.db,
            entity_type="alert",
            entity_id=alert.id,
            action=AuditAction.SLA_BREACHED,
            field_name="sla_breached_at",
            old_value=None,
            new_value=now,
        )
        logger.warning("SLA breach stamped: alert=%s", alert.id)
        return alert

    async def evaluate_alert(
        self,
        *,
        alert: Alert,
        policy: SLAPolicy,
        now: Optional[datetime] = None,
    ) -> Dict[str, bool]:
        """
        Evaluate a single alert against its policy.
        Returns a summary of what happened: {'escalated': bool, 'breached': bool}.
        Intended for on-demand evaluation (e.g., triggered from an API).
        """
        now = now or datetime.now(timezone.utc)
        elapsed_minutes = (now - alert.triggered_at).total_seconds() / 60
        escalated = False
        breached = False

        if (
            alert.sla_breached_at is None
            and elapsed_minutes >= policy.resolution_minutes
        ):
            await self.mark_sla_breach(alert=alert, now=now)
            breached = True

        if alert.escalation_level < 2 and elapsed_minutes >= policy.escalation_level_2_minutes:
            await self.escalate_alert(alert=alert, new_level=2, now=now)
            escalated = True
        elif alert.escalation_level < 1 and elapsed_minutes >= policy.escalation_level_1_minutes:
            await self.escalate_alert(alert=alert, new_level=1, now=now)
            escalated = True

        return {"escalated": escalated, "breached": breached}

    # ------------------------------------------------------------------
    # Internal notification helper
    # ------------------------------------------------------------------

    async def _notify_users(
        self,
        *,
        organization_id: uuid.UUID,
        active_users: Sequence[User],
        notification_type: str,
        title: str,
        message: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[uuid.UUID] = None,
    ) -> None:
        """Broadcast notifications to org users via NotificationService."""
        notif_svc = NotificationService(db=self.db)
        count = await notif_svc.create_for_org_users(
            organization_id=organization_id,
            active_users=active_users,
            notification_type=notification_type,
            title=title,
            message=message,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        if count > 0:
            logger.info(
                "Notifications sent: type=%s entity=%s count=%d",
                notification_type, related_entity_id, count,
            )
