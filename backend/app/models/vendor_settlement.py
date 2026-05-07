import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, ForeignKey, UUID, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .vendor import Vendor
    from .invoice import Invoice
    from .payment import Payment

class SettlementStatus(str, Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class VendorSettlement(FullBaseModel):
    """
    Vendor Settlement model representing a workflow-safe financial closure layer.
    """
    __tablename__ = "vendor_settlement"
    
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendor.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    settlement_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False
    )
    
    settlement_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    status: Mapped[SettlementStatus] = mapped_column(
        String(20),
        default=SettlementStatus.PENDING,
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "settlement_reference",
            name="uq_vendor_settlement_reference_per_org"
        ),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    vendor: Mapped["Vendor"] = relationship("Vendor")
    invoice: Mapped["Invoice"] = relationship("Invoice")
    payment: Mapped["Payment"] = relationship("Payment")

    def __repr__(self) -> str:
        return f"<VendorSettlement(vendor_id={self.vendor_id}, payment_id={self.payment_id}, amount={self.amount}, status={self.status})>"
