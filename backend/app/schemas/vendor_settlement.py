import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.vendor_settlement import SettlementStatus

class VendorSettlementBase(BaseModel):
    settlement_reference: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, decimal_places=4)
    settlement_date: Optional[datetime] = None
    notes: Optional[str] = None

class VendorSettlementCreate(VendorSettlementBase):
    vendor_id: uuid.UUID
    invoice_id: uuid.UUID
    payment_id: uuid.UUID

class VendorSettlementUpdate(BaseModel):
    settlement_reference: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    settlement_date: Optional[datetime] = None
    notes: Optional[str] = None

class VendorSettlementStatusUpdate(BaseModel):
    status: SettlementStatus

class VendorSettlementResponse(VendorSettlementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    vendor_id: uuid.UUID
    invoice_id: uuid.UUID
    payment_id: uuid.UUID
    status: SettlementStatus
    settlement_date: datetime
    created_at: datetime
    updated_at: datetime

class VendorSettlementListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    vendor_id: uuid.UUID
    invoice_id: uuid.UUID
    payment_id: uuid.UUID
    settlement_reference: str
    amount: Decimal
    status: SettlementStatus
    settlement_date: datetime
    created_at: datetime
