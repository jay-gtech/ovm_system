"""
Notification Service
====================
Centralized delivery layer for operational notifications.

Architecture:
- create_notification()   — creates an IN_APP record (always succeeds locally)
- send_email_placeholder()— logs intent; real SMTP wired in a future sprint
- mark_read()             — transitions SENT/PENDING → READ

Transaction contract: callers commit; this service only flushes.

Deduplication: check NotificationRepository.find_recent() before calling
create_notification() so repeated escalation/breach events don't spam users.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction
from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationType
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

# Deduplication window: suppress repeat notifications of the same type for the
# same entity per user within this window.  Keeps the inbox clean during
# repeated scheduler cycles.
_DEDUP_WINDOW_MINUTES: int = 120


class NotificationService:
    """
    Centralized notification lifecycle service.

    Transaction contract: callers are responsible for commit().
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = NotificationRepository()

    # ------------------------------------------------------------------
    # Core creation
    # ------------------------------------------------------------------

    async def create_notification(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str,
        channel: str = NotificationChannel.IN_APP,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[uuid.UUID] = None,
        skip_dedup_check: bool = False,
    ) -> Optional[Notification]:
        """
        Create a notification with deduplication protection.

        Returns the created Notification, or None if a recent duplicate exists.
        Set skip_dedup_check=True only for system-critical events that must
        always deliver (e.g., first-time SLA breach).
        """
        if not skip_dedup_check and related_entity_id is not None:
            since = datetime.now(timezone.utc) - timedelta(minutes=_DEDUP_WINDOW_MINUTES)
            existing = await self._repo.find_recent(
                self.db,
                organization_id=organization_id,
                user_id=user_id,
                notification_type=notification_type,
                related_entity_id=related_entity_id,
                since=since,
            )
            if existing is not None:
                return None  # deduplicated

        now = datetime.now(timezone.utc)
        notif = await self._repo.create(self.db, obj_in={
            "organization_id": organization_id,
            "user_id": user_id,
            "notification_type": notification_type,
            "channel": channel,
            "title": title,
            "message": message,
            "status": NotificationStatus.SENT,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "sent_at": now,
            "retry_count": 0,
        })
        return notif

    async def create_for_org_users(
        self,
        *,
        organization_id: uuid.UUID,
        active_users: Sequence[User],
        notification_type: str,
        title: str,
        message: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[uuid.UUID] = None,
    ) -> int:
        """
        Broadcast an IN_APP notification to all provided active users.

        Uses per-user deduplication to avoid inbox spam when the scanner
        runs multiple cycles before an alert is acknowledged.

        Returns the count of notifications actually created.
        """
        created = 0
        for user in active_users:
            result = await self.create_notification(
                organization_id=organization_id,
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                message=message,
                channel=NotificationChannel.IN_APP,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
            )
            if result is not None:
                created += 1
        return created

    # ------------------------------------------------------------------
    # Email placeholder
    # ------------------------------------------------------------------

    async def send_email_placeholder(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
        notification_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Placeholder for transactional email delivery.

        Logs the intent at INFO level.  Wire a real SMTP provider (SendGrid,
        SES, Postmark) here when the notification delivery sprint ships.

        Returns True (simulating success) so callers can update status.
        """
        logger.info(
            "EMAIL_PLACEHOLDER to=%s subject=%r notification_id=%s",
            to_email, subject, notification_id,
        )
        return True

    # ------------------------------------------------------------------
    # Read lifecycle
    # ------------------------------------------------------------------

    async def mark_read(
        self,
        *,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification:
        """
        Mark a notification as READ.

        Validates that the notification belongs to user_id to prevent
        cross-user read marking (belt-and-suspenders on top of tenant scope).
        Raises ValueError if not found or if it belongs to a different user.
        """
        notif = await self._repo.get(self.db, notification_id)
        if notif is None:
            raise ValueError(f"Notification {notification_id} not found.")
        if notif.user_id != user_id:
            raise ValueError("Cannot mark another user's notification as read.")

        if notif.status == NotificationStatus.READ:
            return notif  # idempotent — already read

        now = datetime.now(timezone.utc)
        updated = await self._repo.update(self.db, db_obj=notif, obj_in={
            "status": NotificationStatus.READ,
            "read_at": now,
        })
        await AuditService.log_event(
            self.db,
            entity_type="notification",
            entity_id=notification_id,
            action=AuditAction.NOTIFICATION_READ,
            actor_user_id=user_id,
            field_name="status",
            old_value=notif.status,
            new_value=NotificationStatus.READ,
        )
        return updated

    async def mark_failed(
        self,
        *,
        notification_id: uuid.UUID,
    ) -> Notification:
        """Increment retry_count and transition to FAILED."""
        notif = await self._repo.get(self.db, notification_id)
        if notif is None:
            raise ValueError(f"Notification {notification_id} not found.")
        updated = await self._repo.update(self.db, db_obj=notif, obj_in={
            "status": NotificationStatus.FAILED,
            "retry_count": notif.retry_count + 1,
        })
        await AuditService.log_event(
            self.db,
            entity_type="notification",
            entity_id=notification_id,
            action=AuditAction.NOTIFICATION_FAILED,
        )
        return updated
