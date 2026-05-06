import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .role import Role
    from .audit_log import AuditLog


class User(FullBaseModel):
    """
    User model representing an account within an organization.
    Email uniqueness is scoped per-tenant: the same email may exist in
    multiple organizations (standard multi-tenant SaaS pattern).
    """
    __table_args__ = (
        # Composite unique: one email per organization, not globally unique.
        UniqueConstraint("organization_id", "email", name="uq_user_organization_id_email"),
    )

    # No unique=True here — uniqueness is enforced by the composite constraint above.
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    # Argon2id PHC string format can exceed 255 chars; 1024 is safe headroom.
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="users"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_role",
        back_populates="users"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(email={self.email}, full_name={self.full_name})>"
