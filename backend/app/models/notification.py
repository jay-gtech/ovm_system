import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, UUID, ForeignKey, DateTime, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import TenantBaseModel

if TYPE_CHECKING:
    from .user import User


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    READ = "READ"


class NotificationType(str, Enum):
    ALERT_ESCALATED = "ALERT_ESCALATED"
    SLA_BREACHED = "SLA_BREACHED"
    CRITICAL_EXPOSURE = "CRITICAL_EXPOSURE"
    UNRESOLVED_HIGH_RISK = "UNRESOLVED_HIGH_RISK"


class Notification(TenantBaseModel):
    """
    Operational notification for a single user within a tenant.

    Design rules:
    - Append-oriented: no soft-delete; records accumulate as an operational log.
    - Tenant-isolated: organization_id scopes all reads and writes.
    - Retry-safe: retry_count tracks delivery attempts; callers increment on failure.
    - Channel-extensible: channel field allows adding SMS/webhook without schema changes.
    - Deduplication: callers check for recent same-type/entity notifications before
      creating new ones (NotificationRepository.find_recent).
    """

    __table_args__ = (
        # Fast lookup for per-user unread count (used by notification bell).
        Index("ix_notification_user_status", "user_id", "status"),
        # Tenant + recency scan used by deduplication guard.
        Index(
            "ix_notification_org_entity",
            "organization_id", "notification_type", "related_entity_id",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    channel: Mapped[str] = mapped_column(
        String(20), default=NotificationChannel.IN_APP, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=NotificationStatus.PENDING, index=True, nullable=False
    )
    # Polymorphic reference to the related operational entity (alert, invoice, etc.)
    related_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Number of delivery attempts; incremented by NotificationService on failure.
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recipient: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Notification(type={self.notification_type}, "
            f"channel={self.channel}, status={self.status})>"
        )
