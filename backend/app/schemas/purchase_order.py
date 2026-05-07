import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.purchase_order import PurchaseOrderStatus

# --- Line Item Schemas ---

class POLineItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(gt=0, decimal_places=4)

class POLineItemCreate(POLineItemBase):
    pass

class POLineItemResponse(POLineItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    purchase_order_id: uuid.UUID
    product_sku_snapshot: str
    product_name_snapshot: str
    unit_price_snapshot: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

# --- Purchase Order Schemas ---

class PurchaseOrderBase(BaseModel):
    vendor_id: uuid.UUID
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    po_number: str = Field(min_length=1, max_length=50)
    line_items: List[POLineItemCreate] = Field(min_length=1)

class PurchaseOrderUpdate(BaseModel):
    notes: Optional[str] = None

class PurchaseOrderStatusUpdate(BaseModel):
    status: PurchaseOrderStatus

class PurchaseOrderResponse(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    po_number: str
    status: PurchaseOrderStatus
    subtotal_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    line_items: List[POLineItemResponse]

class PurchaseOrderListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    po_number: str
    vendor_id: uuid.UUID
    status: PurchaseOrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
