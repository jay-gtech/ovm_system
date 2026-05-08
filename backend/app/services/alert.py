import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.models.audit_log import AuditAction
from app.repositories.alert import AlertRepository
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


# Allowed status transitions — terminal state RESOLVED has an empty set.
_VALID_TRANSITIONS: Dict[AlertStatus, set] = {
    AlertStatus.OPEN: {AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED},
    AlertStatus.ACKNOWLEDGED: {AlertStatus.RESOLVED},
    AlertStatus.RESOLVED: set(),
}


def _safe_json(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively make a dict JSON-safe (handles Decimal, UUID)."""
    if data is None:
        return None
    result: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, Decimal):
            result[k] = str(v)
        elif isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif isinstance(v, dict):
            result[k] = _safe_json(v)
        elif isinstance(v, list):
            result[k] = [
                _safe_json(i) if isinstance(i, dict) else
                (str(i) if isinstance(i, (Decimal, uuid.UUID)) else i)
                for i in v
            ]
        else:
            result[k] = v
    return result


class AlertService:
    """
    Centralized operational alert lifecycle service.

    Transaction contract: callers (endpoints, scanner jobs) are responsible for
    calling commit().  This service flushes inside repository operations but
    never commits — preserving the UoW pattern used elsewhere.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = AlertRepository()

    async def create_alert(
        self,
        *,
        organization_id: uuid.UUID,
        alert_type: str,
        severity: str,
        entity_type: str,
        entity_id: uuid.UUID,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Alert]:
        """
        Create an operational alert with deduplication protection.

        Returns the newly created Alert, or None if an active (OPEN or
        ACKNOWLEDGED) alert already exists for the same issue — prevents
        duplicate scanner spam across scheduler runs.

        A RESOLVED alert is NOT considered active: if the underlying issue
        reappears after resolution, a fresh alert is created.
        """
        existing = await self._repo.find_active(
            self.db,
            organization_id=organization_id,
            alert_type=alert_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if existing is not None:
            return None  # deduplicated — silent skip

        now = datetime.now(timezone.utc)
        try:
            alert = await self._repo.create(self.db, obj_in={
                "organization_id": organization_id,
                "alert_type": alert_type,
                "severity": severity,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": title,
                "message": message,
                "status": AlertStatus.OPEN,
                "triggered_at": now,
                "metadata_json": _safe_json(metadata),
            })
        except IntegrityError:
            # Two concurrent scanner runs both passed the application-level
            # find_active() check before either INSERT committed.  The partial
            # unique index uq_alert_active_dedup rejects the second write.
            # Treat it as a successful deduplication — same outcome as the
            # application-level path.
            logger.warning(
                "DB-level dedup blocked concurrent alert creation: "
                "org=%s type=%s entity=%s/%s",
                organization_id, alert_type, entity_type, entity_id,
            )
            await self.db.rollback()
            return None
        return alert

    async def acknowledge_alert(
        self,
        *,
        alert_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Alert:
        """
        Transition OPEN → ACKNOWLEDGED.

        Raises ValueError for invalid transitions (wrong status, not found).
        """
        alert = await self._repo.get(self.db, alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found.")

        current = AlertStatus(alert.status)
        if AlertStatus.ACKNOWLEDGED not in _VALID_TRANSITIONS[current]:
            raise ValueError(
                f"Cannot acknowledge an alert in '{alert.status}' status. "
                "Only OPEN alerts may be acknowledged."
            )

        now = datetime.now(timezone.utc)
        updated = await self._repo.update(self.db, db_obj=alert, obj_in={
            "status": AlertStatus.ACKNOWLEDGED,
            "acknowledged_at": now,
            "acknowledged_by_user_id": user_id,
        })
        await AuditService.log_event(
            self.db,
            entity_type="alert",
            entity_id=alert.id,
            action=AuditAction.ALERT_ACKNOWLEDGED,
            actor_user_id=user_id,
            field_name="status",
            old_value=AlertStatus.OPEN,
            new_value=AlertStatus.ACKNOWLEDGED,
        )
        return updated

    async def bulk_acknowledge(
        self,
        *,
        user_id: uuid.UUID,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
    ) -> int:
        """
        Acknowledge all OPEN alerts for the current tenant in a single transaction.

        Optional filters narrow the scope (severity and/or alert_type).
        Tenant isolation is enforced by apply_tenant_scope inside get_multi().
        Returns the count of alerts transitioned.

        Safe properties:
          - Single transaction: all updates or none (rollback on error).
          - Tenant-scoped: only the current JWT tenant's alerts are touched.
          - Pagination-independent: fetches ALL matching OPEN alerts, not just
            the current page displayed in the UI.
          - RBAC: enforced at the endpoint layer before this method is called.
        """
        open_alerts = await self._repo.get_multi(
            self.db,
            skip=0,
            limit=10_000,  # practical upper bound; storm protection caps creation
            status=AlertStatus.OPEN,
            severity=severity,
            alert_type=alert_type,
        )
        now = datetime.now(timezone.utc)
        count = 0
        for alert in open_alerts:
            await self._repo.update(self.db, db_obj=alert, obj_in={
                "status": AlertStatus.ACKNOWLEDGED,
                "acknowledged_at": now,
                "acknowledged_by_user_id": user_id,
            })
            count += 1
        return count

    async def resolve_alert(
        self,
        *,
        alert_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Alert:
        """
        Transition OPEN|ACKNOWLEDGED → RESOLVED.

        Raises ValueError for invalid transitions or if alert is not found.
        RESOLVED is terminal — re-resolving is rejected.
        """
        alert = await self._repo.get(self.db, alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found.")

        current = AlertStatus(alert.status)
        if AlertStatus.RESOLVED not in _VALID_TRANSITIONS[current]:
            raise ValueError(
                f"Cannot resolve an alert in '{alert.status}' status. "
                "RESOLVED alerts cannot be transitioned further."
            )

        old_status = alert.status
        now = datetime.now(timezone.utc)
        updated = await self._repo.update(self.db, db_obj=alert, obj_in={
            "status": AlertStatus.RESOLVED,
            "resolved_at": now,
            "resolved_by_user_id": user_id,
        })
        await AuditService.log_event(
            self.db,
            entity_type="alert",
            entity_id=alert.id,
            action=AuditAction.ALERT_RESOLVED,
            actor_user_id=user_id,
            field_name="status",
            old_value=old_status,
            new_value=AlertStatus.RESOLVED,
        )
        return updated
