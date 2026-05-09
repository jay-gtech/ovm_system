import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, UUID, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.db.mixins import UUIDMixin

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class AuditAction(str, Enum):
    # Generic operations
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    # Auth events
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ACCESS = "ACCESS"
    # Invoice workflow
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_UPDATED = "INVOICE_UPDATED"
    INVOICE_STATUS_CHANGED = "INVOICE_STATUS_CHANGED"
    INVOICE_CANCELLED = "INVOICE_CANCELLED"
    # Payment workflow
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_CANCELLED = "PAYMENT_CANCELLED"
    PAYMENT_STATUS_CHANGED = "PAYMENT_STATUS_CHANGED"
    # Settlement workflow
    SETTLEMENT_CREATED = "SETTLEMENT_CREATED"
    SETTLEMENT_APPROVED = "SETTLEMENT_APPROVED"
    SETTLEMENT_COMPLETED = "SETTLEMENT_COMPLETED"
    SETTLEMENT_CANCELLED = "SETTLEMENT_CANCELLED"
    SETTLEMENT_STATUS_CHANGED = "SETTLEMENT_STATUS_CHANGED"
    # Vendor operational changes
    VENDOR_CREATED = "VENDOR_CREATED"
    VENDOR_UPDATED = "VENDOR_UPDATED"
    VENDOR_STATUS_CHANGED = "VENDOR_STATUS_CHANGED"
    VENDOR_PAYMENT_TERMS_CHANGED = "VENDOR_PAYMENT_TERMS_CHANGED"
    VENDOR_BANK_DETAILS_CHANGED = "VENDOR_BANK_DETAILS_CHANGED"
    # Alert lifecycle
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    # SLA / escalation
    ALERT_ESCALATED = "ALERT_ESCALATED"
    SLA_BREACHED = "SLA_BREACHED"
    SLA_POLICY_CREATED = "SLA_POLICY_CREATED"
    SLA_POLICY_UPDATED = "SLA_POLICY_UPDATED"
    # Notification lifecycle
    NOTIFICATION_READ = "NOTIFICATION_READ"
    NOTIFICATION_FAILED = "NOTIFICATION_FAILED"
    # Risk intelligence
    RISK_ASSESSMENT_GENERATED = "RISK_ASSESSMENT_GENERATED"
    RISK_CRITICAL_CLASSIFIED = "RISK_CRITICAL_CLASSIFIED"
    RISK_LEVEL_ESCALATED = "RISK_LEVEL_ESCALATED"


class AuditLog(Base, UUIDMixin):
    """
    Immutable append-only audit trail for all financial and operational events.

    Design invariants:
    - No updated_at: records are never modified after creation.
    - No is_deleted / deleted_at: records are never soft-deleted.
    - No UPDATE or DELETE API endpoints exist for this model.
    - Tenant-scoped via organization_id for strict multi-tenant isolation.
    - field_name + old_value + new_value support field-level change granularity.
    """

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Field-level granularity: set for UPDATE events, null for CREATE/DELETE
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Actor identity
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Operational context
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    # Composite indexes for high-cardinality financial queries
    __table_args__ = (
        Index("ix_audit_log_entity_lookup", "organization_id", "entity_type", "entity_id"),
        Index("ix_audit_log_tenant_time", "organization_id", "created_at"),
        Index("ix_audit_log_actor_lookup", "organization_id", "actor_user_id"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_logs")
    # 'user' attribute name kept for back_populates="audit_logs" compatibility on User model
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog(action={self.action}, entity_type={self.entity_type}, "
            f"entity_id={self.entity_id})>"
        )
