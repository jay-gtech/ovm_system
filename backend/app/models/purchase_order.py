import uuid
from decimal import Decimal
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, UniqueConstraint, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .vendor import Vendor
    from .product import Product

class PurchaseOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SENT = "SENT"
    CANCELLED = "CANCELLED"

class PurchaseOrder(FullBaseModel):
    """
    Purchase Order model representing a procurement request.
    
    Financial Rules:
    - po_number is immutable and MUST be unique per tenant (organization_id).
    - vendor_id must belong to the same tenant.
    - totals (subtotal_amount, total_amount) are calculated server-side.
    - Hard deletes are disabled via SoftDeleteMixin.
    """
    __table_args__ = (
        UniqueConstraint(
            "organization_id", 
            "po_number", 
            name="uq_purchase_order_organization_id_po_number"
        ),
    )

    po_number: Mapped[str] = mapped_column(
        String(50), 
        index=True, 
        nullable=False
    )
    
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendor.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20), 
        default=PurchaseOrderStatus.DRAFT, 
        nullable=False
    )
    
    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        default=Decimal("0.0000"),
        nullable=False
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        default=Decimal("0.0000"),
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    vendor: Mapped["Vendor"] = relationship("Vendor")
    line_items: Mapped[List["POLineItem"]] = relationship(
        "POLineItem", 
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(po_number={self.po_number}, status={self.status})>"

class POLineItem(FullBaseModel):
    """
    Line item for a Purchase Order.
    
    Financial Rules:
    - product_id must belong to the same tenant.
    - snapshots are mandatory at creation to preserve historical data.
    - line_total is calculated server-side (quantity * unit_price_snapshot).
    """
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    # Snapshots to preserve data even if the product record changes or is deleted
    product_sku_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", 
        back_populates="line_items"
    )
    product: Mapped["Product"] = relationship("Product")

    def __repr__(self) -> str:
        return f"<POLineItem(po_id={self.purchase_order_id}, product_sku={self.product_sku_snapshot})>"
