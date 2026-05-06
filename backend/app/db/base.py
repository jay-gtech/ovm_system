from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

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

class FullBaseModel(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Complete base model with Soft Delete and Tenant isolation.
    """
    __abstract__ = True
