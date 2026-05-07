import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.invoice import InvoiceStatus

# --- Line Item Schemas ---

class InvoiceLineItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(gt=0, decimal_places=4)

class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass

class InvoiceLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    invoice_id: uuid.UUID
    product_id: uuid.UUID
    product_sku_snapshot: str
    product_name_snapshot: str
    unit_price_snapshot: Decimal
    quantity_snapshot: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

# --- Invoice Schemas ---

class InvoiceBase(BaseModel):
    vendor_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    invoice_number: str = Field(min_length=1, max_length=50)
    line_items: List[InvoiceLineItemCreate] = Field(min_length=1)

class InvoiceUpdate(BaseModel):
    notes: Optional[str] = None

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus

class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_number: str
    status: InvoiceStatus
    subtotal_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    created_at: datetime
    updated_at: datetime
    line_items: List[InvoiceLineItemResponse]

class InvoiceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_number: str
    vendor_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    status: InvoiceStatus
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    created_at: datetime
    updated_at: datetime
