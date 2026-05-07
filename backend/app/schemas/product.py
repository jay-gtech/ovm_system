from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    unit_price: Decimal = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    vendor_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class ProductCreate(ProductBase):
    sku: str = Field(..., min_length=1, max_length=100)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    vendor_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class ProductStatusUpdate(BaseModel):
    status: ProductStatus

class ProductResponse(ProductBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    sku: str
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int
