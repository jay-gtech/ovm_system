import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.api import deps
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    PaymentStatusUpdate
)
from app.services.payment import PaymentService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

def get_payment_service(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow)
) -> PaymentService:
    return PaymentService(uow)

@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_payment(
    *,
    service: PaymentService = Depends(get_payment_service),
    data: PaymentCreate
):
    """
    Register a new payment for an invoice.
    - Validates invoice ownership.
    - Cumulative payments cannot exceed invoice total.
    """
    return await service.create_payment(data)

@router.get("", response_model=List[PaymentListResponse])
async def list_payments(
    service: PaymentService = Depends(get_payment_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List all payments for the current tenant."""
    return await service.get_multi(skip=skip, limit=limit)

@router.get("/{id}", response_model=PaymentResponse)
async def get_payment(
    id: uuid.UUID,
    service: PaymentService = Depends(get_payment_service),
):
    """Get a specific payment record."""
    return await service.get_by_id(id)

@router.patch("/{id}/status", response_model=PaymentResponse)
async def update_payment_status(
    id: uuid.UUID,
    status_update: PaymentStatusUpdate,
    service: PaymentService = Depends(get_payment_service),
):
    """
    Update payment status.
    - RECEIVED status triggers overpayment check and invoice status update.
    """
    return await service.update_status(id, status_update.status)

@router.get("/invoice/{invoice_id}", response_model=List[PaymentListResponse])
async def get_invoice_payments(
    invoice_id: uuid.UUID,
    service: PaymentService = Depends(get_payment_service),
):
    """List all payments linked to a specific invoice."""
    return await service.get_by_invoice(invoice_id)
