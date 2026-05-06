import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UUID, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

class UUIDMixin:
    """
    Mixin to add a UUID primary key to a model.
    Note: index=True is redundant on Primary Key and removed for optimization.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps.
    Using timezone-aware datetimes.
    
    updated_at: Managed by SQLAlchemy 'onupdate' at the ORM level.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class TenantMixin:
    """
    Mixin for multi-tenant isolation.
    Every tenant-owned entity must have an organization_id.
    """
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    """
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

class AuditMixin:
    """
    Mixin to track who created and modified the record.
    Useful for future audit logging.
    """
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
