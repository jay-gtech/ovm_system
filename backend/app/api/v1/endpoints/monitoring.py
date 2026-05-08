from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, check_role
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
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["ADMIN", "MANAGER", "ACCOUNTS"])),
):
    """
    Retrieve invoices with an outstanding balance > 0, tracking aging days and overdue status.
    """
    service = MonitoringService(db=db)
    return await service.get_outstanding_invoices(limit=limit, offset=offset)

@router.get("/pending-payments", response_model=List[PendingPaymentResponse])
async def get_pending_payments(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["ADMIN", "MANAGER", "ACCOUNTS"])),
):
    """
    Retrieve payments that are in a PENDING state and waiting to be received.
    """
    service = MonitoringService(db=db)
    return await service.get_pending_payments(limit=limit, offset=offset)

@router.get("/unsettled-payments", response_model=List[UnsettledPaymentResponse])
async def get_unsettled_payments(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["ADMIN", "MANAGER", "ACCOUNTS"])),
):
    """
    Retrieve payments that have been RECEIVED but whose full amount has not yet been settled.
    """
    service = MonitoringService(db=db)
    return await service.get_unsettled_payments(limit=limit, offset=offset)

@router.get("/pending-settlements", response_model=List[PendingSettlementResponse])
async def get_pending_settlements(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["ADMIN", "MANAGER", "ACCOUNTS"])),
):
    """
    Retrieve vendor settlements that are pending operational closure.
    """
    service = MonitoringService(db=db)
    return await service.get_pending_settlements(limit=limit, offset=offset)

@router.get("/financial-summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["ADMIN", "MANAGER", "ACCOUNTS"])),
):
    """
    Retrieve a consolidated financial summary of outstanding operational exposure.
    """
    service = MonitoringService(db=db)
    return await service.get_financial_summary()
