import uuid
from decimal import Decimal
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, Numeric, UniqueConstraint, ForeignKey, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .purchase_order import PurchaseOrder, POLineItem

class GRNStatus(str, Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class GRN(FullBaseModel):
    """
    Goods Receipt Note (GRN) model representing a delivery against a Purchase Order.
    
    Required fields:
    - id (FullBaseModel)
    - organization_id (FullBaseModel/TenantMixin)
    - po_id
    - grn_number
    - receipt_date
    - received_by
    - warehouse_notes
    - status
    - total_received_qty
    - created_at (FullBaseModel/TimestampMixin)
    - updated_at (FullBaseModel/TimestampMixin)
    """
    __tablename__ = "grn"
    
    __table_args__ = (
        UniqueConstraint(
            "organization_id", 
            "grn_number", 
            name="uq_grn_organization_id_grn_number"
        ),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    grn_number: Mapped[str] = mapped_column(
        String(50), 
        index=True, 
        nullable=False
    )
    
    receipt_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    received_by: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    
    warehouse_notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    status: Mapped[GRNStatus] = mapped_column(
        String(20), 
        default=GRNStatus.DRAFT, 
        nullable=False
    )
    
    total_received_qty: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        default=Decimal("0.0000"),
        nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder")
    line_items: Mapped[List["GRNLineItem"]] = relationship(
        "GRNLineItem", 
        back_populates="grn",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<GRN(grn_number={self.grn_number}, status={self.status})>"

class GRNLineItem(FullBaseModel):
    """
    Line item for a Goods Receipt Note.
    
    Required fields:
    - product_code
    - qty_ordered
    - qty_received
    - qty_damaged
    - qty_pending
    """
    __tablename__ = "grn_line_item"
    
    grn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grn.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    po_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("p_o_line_item.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    
    qty_ordered: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )
    
    qty_received: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )
    
    qty_damaged: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        default=Decimal("0.0000"),
        nullable=False
    )
    
    qty_pending: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=False
    )

    # Relationships
    grn: Mapped["GRN"] = relationship(
        "GRN", 
        back_populates="line_items"
    )
    po_line_item: Mapped["POLineItem"] = relationship("POLineItem")

    def __repr__(self) -> str:
        return f"<GRNLineItem(grn_id={self.grn_id}, product_code={self.product_code})>"
