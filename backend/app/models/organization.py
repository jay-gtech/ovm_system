from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .audit_log import AuditLog


class Organization(BaseModel):
    """
    Organization model representing a tenant in the system.
    """
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="organization",
        # NEVER cascade-delete audit logs. The RESTRICT FK on AuditLog.organization_id
        # is the enforcement gate. passive_deletes=True tells SQLAlchemy to let the DB
        # raise the FK violation instead of trying to NULL/delete child rows in Python.
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Organization(name={self.name}, slug={self.slug})>"
