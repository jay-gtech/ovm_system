import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.payment import PaymentStatus, PaymentMethod

class PaymentBase(BaseModel):
    payment_reference: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, decimal_places=4)
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    invoice_id: uuid.UUID
    # status is intentionally absent — always server-assigned to PENDING at creation
    # Use PATCH /{id}/status to advance payment status.

class PaymentUpdate(BaseModel):
    payment_reference: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus

class PaymentResponse(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    status: PaymentStatus
    payment_date: datetime
    created_at: datetime
    updated_at: datetime

class PaymentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    payment_reference: str
    amount: Decimal
    status: PaymentStatus
    payment_date: datetime
    created_at: datetime
