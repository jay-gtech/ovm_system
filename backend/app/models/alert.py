import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import String, Text, UUID, ForeignKey, DateTime, Index, Integer, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import TenantBaseModel

if TYPE_CHECKING:
    from .user import User


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    OVERDUE_INVOICE = "OVERDUE_INVOICE"
    UNSETTLED_VENDOR_LIABILITY = "UNSETTLED_VENDOR_LIABILITY"
    WORKFLOW_STALL = "WORKFLOW_STALL"
    HIGH_FINANCIAL_EXPOSURE = "HIGH_FINANCIAL_EXPOSURE"


class Alert(TenantBaseModel):
    """
    Operational alert — append-oriented, no soft-delete.

    Deduplication invariant: at most one OPEN or ACKNOWLEDGED alert may exist
    per (organization_id, alert_type, entity_type, entity_id) at any time.
    The AlertService enforces this before insert.

    Status transitions (strictly enforced by AlertService):
        OPEN → ACKNOWLEDGED
        OPEN → RESOLVED
        ACKNOWLEDGED → RESOLVED
        RESOLVED → (terminal — no further transitions)
    """

    __table_args__ = (
        # DB-level deduplication guarantee (concurrency-safe).
        # Prevents two concurrent scanner runs from inserting duplicate active alerts
        # for the same (tenant, alert_type, entity). RESOLVED alerts are excluded so
        # the same entity can be re-alerted after the original issue is resolved.
        Index(
            "uq_alert_active_dedup",
            "organization_id", "alert_type", "entity_type", "entity_id",
            unique=True,
            postgresql_where=text("status IN ('OPEN', 'ACKNOWLEDGED')"),
        ),
        # Composite read index for the deduplication lookup and per-tenant filtered lists.
        Index(
            "ix_alert_tenant_type_entity",
            "organization_id", "alert_type", "entity_type", "entity_id",
        ),
        # Supports status-filtered list queries ordered by recency.
        Index("ix_alert_status_triggered", "status", "triggered_at"),
    )

    alert_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    # Generic UUID reference — not a FK because entity_type determines the table.
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=AlertStatus.OPEN, index=True, nullable=False
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # ------------------------------------------------------------------
    # SLA / Escalation fields (Task 2)
    # ------------------------------------------------------------------
    # 0 = not yet escalated; 1 = escalated once; 2 = critically escalated.
    # Transitions are append-only (no downgrade) and enforced by SLAService.
    escalation_level: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )
    # Timestamp of the first escalation (set once; never reset).
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Timestamp when the resolution SLA window expired (set once; never reset).
    sla_breached_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    acknowledged_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[acknowledged_by_user_id]
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by_user_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Alert(type={self.alert_type}, severity={self.severity}, "
            f"status={self.status}, entity={self.entity_type}:{self.entity_id})>"
        )
