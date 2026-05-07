import uuid
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization

class VendorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class Vendor(FullBaseModel):
    """
    Vendor model representing a third-party supplier or service provider.
    
    Financial Rule:
    - vendor_code is immutable and MUST be unique per tenant (organization_id).
    - Hard deletes are disabled; SoftDeleteMixin handles state lifecycle.
    """
    __table_args__ = (
        UniqueConstraint(
            "organization_id", 
            "vendor_code", 
            name="uq_vendor_organization_id_vendor_code"
        ),
    )

    vendor_code: Mapped[str] = mapped_column(
        String(50), 
        index=True, 
        nullable=False
    )
    legal_name: Mapped[str] = mapped_column(
        String(255), 
        index=True, 
        nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50), 
        index=True, 
        nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    status: Mapped[VendorStatus] = mapped_column(
        String(20), 
        default=VendorStatus.ACTIVE, 
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

    def __repr__(self) -> str:
        return f"<Vendor(vendor_code={self.vendor_code}, legal_name={self.legal_name})>"
