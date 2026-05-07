import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, UniqueConstraint, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .vendor import Vendor

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Product(FullBaseModel):
    """
    Product model representing an item in the catalog.
    
    Financial Rules:
    - SKU is immutable and MUST be unique per tenant (organization_id).
    - vendor_id must belong to the same tenant.
    - unit_price must be validated at the service layer.
    - Hard deletes are disabled via SoftDeleteMixin.
    """
    __table_args__ = (
        UniqueConstraint(
            "organization_id", 
            "sku", 
            name="uq_product_organization_id_sku"
        ),
    )

    sku: Mapped[str] = mapped_column(
        String(100), 
        index=True, 
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255), 
        index=True, 
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), 
        index=True, 
        nullable=True
    )
    
    # Financial data
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3), 
        default="USD", 
        nullable=False
    )
    
    # Relationships & Lifecycle
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendor.id", ondelete="RESTRICT"),
        index=True,
        nullable=True
    )
    
    status: Mapped[ProductStatus] = mapped_column(
        String(20), 
        default=ProductStatus.ACTIVE, 
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")

    def __repr__(self) -> str:
        return f"<Product(sku={self.sku}, name={self.name})>"
