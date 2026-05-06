import re
from typing import Any
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

# Production-grade naming conventions for constraints
# This ensures Alembic can reliably detect and name constraints
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate __tablename__ automatically from class name.
        Example: UserAccount -> user_account
        """
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


# Imported after Base so the dependency direction is unambiguous:
# Base defines the metadata; mixins attach columns to it via mapped_column.
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin, AuditMixin  # noqa: E402


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base for all non-tenant specific models.
    Includes UUID PK and Timestamps.
    """
    __abstract__ = True


class TenantBaseModel(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Base for all tenant-specific models.
    Includes UUID PK, Timestamps, and Organization ID.
    """
    __abstract__ = True


class FullBaseModel(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin, AuditMixin):
    """
    Complete base model with Soft Delete, Tenant isolation, and Audit support.
    """
    __abstract__ = True
