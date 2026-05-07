import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, ForeignKey, UUID, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .invoice import Invoice

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    CHECK = "CHECK"
    OTHER = "OTHER"

class Payment(FullBaseModel):
    """
    Payment model representing a financial transaction received for an invoice.
    
    Financial Rules:
    - Must belong to the same tenant (organization_id) as the invoice.
    - Cumulative RECEIVED payments cannot exceed invoice total.
    - amount must be > 0.
    """
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    payment_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False
    )
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        String(50),
        default=PaymentMethod.BANK_TRANSFER,
        nullable=False
    )
    
    payment_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(invoice_id={self.invoice_id}, amount={self.amount}, status={self.status})>"
