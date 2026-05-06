from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import TenantBaseModel

if TYPE_CHECKING:
    from .user import User


class Role(TenantBaseModel):
    """
    Role model for RBAC.
    Roles are tenant-scoped: each organization manages its own role namespace.
    The same role name (e.g. 'ADMIN') may exist in multiple organizations.
    """
    __table_args__ = (
        # Role names must be unique within a tenant, not globally.
        UniqueConstraint("organization_id", "name", name="uq_role_organization_id_name"),
    )

    # No unique=True here — uniqueness is enforced by the composite constraint above.
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_role",
        back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role(name={self.name})>"
