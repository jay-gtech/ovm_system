import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.grn import GRNStatus

# --- Line Item Schemas ---

class GRNLineItemBase(BaseModel):
    po_line_item_id: uuid.UUID
    product_code: str = Field(min_length=1, max_length=100)
    qty_ordered: Decimal = Field(gt=0, decimal_places=4)
    qty_received: Decimal = Field(ge=0, decimal_places=4)
    qty_damaged: Decimal = Field(ge=0, decimal_places=4, default=Decimal("0.0000"))

class GRNLineItemCreate(GRNLineItemBase):
    pass

class GRNLineItemResponse(GRNLineItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    grn_id: uuid.UUID
    qty_pending: Decimal
    created_at: datetime
    updated_at: datetime

# --- GRN Schemas ---

class GRNBase(BaseModel):
    po_id: uuid.UUID
    received_by: str = Field(min_length=1, max_length=255)
    warehouse_notes: Optional[str] = None
    receipt_date: datetime

class GRNCreate(GRNBase):
    grn_number: str = Field(min_length=1, max_length=50)
    line_items: List[GRNLineItemCreate] = Field(min_length=1)

class GRNUpdate(BaseModel):
    warehouse_notes: Optional[str] = None
    received_by: Optional[str] = None

class GRNStatusUpdate(BaseModel):
    status: GRNStatus

class GRNResponse(GRNBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    grn_number: str
    status: GRNStatus
    total_received_qty: Decimal
    created_at: datetime
    updated_at: datetime
    line_items: List[GRNLineItemResponse]

class GRNListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    grn_number: str
    po_id: uuid.UUID
    status: GRNStatus
    total_received_qty: Decimal
    receipt_date: datetime
    created_at: datetime
    updated_at: datetime
