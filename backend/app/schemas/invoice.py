import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, PlainSerializer
from typing_extensions import Annotated
from app.models.invoice import InvoiceStatus

DecimalStr = Annotated[
    Decimal,
    PlainSerializer(lambda x: str(x) if x is not None else None, return_type=str, when_used="json"),
]

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
    unit_price_snapshot: DecimalStr
    quantity_snapshot: DecimalStr
    line_total: DecimalStr
    created_at: datetime
    updated_at: datetime

# --- Invoice Schemas ---

class InvoiceBase(BaseModel):
    vendor_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    invoice_number: str = Field(min_length=1, max_length=50)
    line_items: List[InvoiceLineItemCreate] = Field(min_length=1)

class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    notes: Optional[str] = None

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus

class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_number: str
    status: InvoiceStatus
    subtotal_amount: DecimalStr
    total_amount: DecimalStr
    paid_amount: DecimalStr
    outstanding_amount: DecimalStr
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
    due_date: Optional[date] = None
    status: InvoiceStatus
    total_amount: DecimalStr
    paid_amount: DecimalStr
    outstanding_amount: DecimalStr
    created_at: datetime
    updated_at: datetime
