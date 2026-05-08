from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.monitoring import (
    OutstandingInvoiceResponse,
    PendingPaymentResponse,
    UnsettledPaymentResponse,
    PendingSettlementResponse,
    FinancialSummaryResponse
)
from app.services.monitoring import MonitoringService

router = APIRouter()

@router.get("/outstanding-invoices", response_model=List[OutstandingInvoiceResponse])
async def get_outstanding_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve invoices with an outstanding balance > 0, tracking aging days and overdue status.
    """
    service = MonitoringService(db=db)
    return await service.get_outstanding_invoices()

@router.get("/pending-payments", response_model=List[PendingPaymentResponse])
async def get_pending_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve payments that are in a PENDING state and waiting to be received.
    """
    service = MonitoringService(db=db)
    return await service.get_pending_payments()

@router.get("/unsettled-payments", response_model=List[UnsettledPaymentResponse])
async def get_unsettled_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve payments that have been RECEIVED but whose full amount has not yet been settled.
    """
    service = MonitoringService(db=db)
    return await service.get_unsettled_payments()

@router.get("/pending-settlements", response_model=List[PendingSettlementResponse])
async def get_pending_settlements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve vendor settlements that are pending operational closure.
    """
    service = MonitoringService(db=db)
    return await service.get_pending_settlements()

@router.get("/financial-summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a consolidated financial summary of outstanding operational exposure.
    """
    service = MonitoringService(db=db)
    return await service.get_financial_summary()
