from datetime import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.vendor import VendorStatus

class VendorBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None

class VendorCreate(VendorBase):
    vendor_code: str = Field(..., min_length=1, max_length=50)
    legal_name: str = Field(..., min_length=1, max_length=255)

class VendorUpdate(VendorBase):
    # legal_name can be updated, but vendor_code is immutable and managed by service layer.
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)

class VendorStatusUpdate(BaseModel):
    status: VendorStatus

class VendorResponse(VendorCreate):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: VendorStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VendorListResponse(BaseModel):
    items: List[VendorResponse]
    total: int
