import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.api import deps
from app.schemas.invoice import (
    InvoiceCreate, 
    InvoiceResponse, 
    InvoiceListResponse,
    InvoiceStatusUpdate
)
from app.services.invoice import InvoiceService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

def get_invoice_service(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow)
) -> InvoiceService:
    return InvoiceService(uow)

@router.post(
    "", 
    response_model=InvoiceResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_invoice(
    *,
    service: InvoiceService = Depends(get_invoice_service),
    data: InvoiceCreate
):
    """
    Create a new Invoice.
    - Validates vendor, products and purchase order belong to tenant.
    - Calculates totals server-side.
    - Snapshots product data.
    """
    return await service.create_invoice(data)

@router.get("", response_model=List[InvoiceListResponse])
async def list_invoices(
    service: InvoiceService = Depends(get_invoice_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List all Invoices for the current tenant."""
    return await service.list_invoices(skip=skip, limit=limit)

@router.get("/{id}", response_model=InvoiceResponse)
async def get_invoice(
    id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
):
    """Get a specific Invoice with line items."""
    return await service.get_invoice(id)

@router.patch("/{id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    id: uuid.UUID,
    status_update: InvoiceStatusUpdate,
    service: InvoiceService = Depends(get_invoice_service),
):
    """
    Update the status of an Invoice.
    Enforces state transition rules.
    """
    return await service.update_invoice_status(id, status_update)
