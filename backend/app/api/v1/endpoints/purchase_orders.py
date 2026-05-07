import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.api import deps
from app.schemas.purchase_order import (
    PurchaseOrderCreate, 
    PurchaseOrderResponse, 
    PurchaseOrderListResponse,
    PurchaseOrderStatusUpdate
)
from app.services.purchase_order import PurchaseOrderService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

def get_po_service(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow)
) -> PurchaseOrderService:
    return PurchaseOrderService(uow)

@router.post(
    "", 
    response_model=PurchaseOrderResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_purchase_order(
    *,
    service: PurchaseOrderService = Depends(get_po_service),
    data: PurchaseOrderCreate
):
    """
    Create a new Purchase Order.
    - Validates vendor and products belong to tenant.
    - Calculates totals server-side.
    - Snapshots product data.
    """
    return await service.create_purchase_order(data)

@router.get("", response_model=List[PurchaseOrderListResponse])
async def list_purchase_orders(
    service: PurchaseOrderService = Depends(get_po_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List all Purchase Orders for the current tenant."""
    return await service.list_purchase_orders(skip=skip, limit=limit)

@router.get("/{id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    id: uuid.UUID,
    service: PurchaseOrderService = Depends(get_po_service),
):
    """Get a specific Purchase Order with line items."""
    return await service.get_purchase_order(id)

@router.patch("/{id}/status", response_model=PurchaseOrderResponse)
async def update_purchase_order_status(
    id: uuid.UUID,
    status_update: PurchaseOrderStatusUpdate,
    service: PurchaseOrderService = Depends(get_po_service),
):
    """
    Update the status of a Purchase Order.
    Enforces state transition rules.
    """
    return await service.update_po_status(id, status_update)
