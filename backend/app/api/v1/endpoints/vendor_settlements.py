import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_uow
from app.schemas.vendor_settlement import (
    VendorSettlementCreate,
    VendorSettlementResponse,
    VendorSettlementListResponse,
    VendorSettlementStatusUpdate,
)
from app.services.vendor_settlement import VendorSettlementService
from app.services.uow import BaseUnitOfWork
from app.models.user import User

router = APIRouter()

@router.post("", response_model=VendorSettlementResponse)
async def create_vendor_settlement(
    *,
    uow: BaseUnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
    settlement_in: VendorSettlementCreate,
) -> Any:
    """
    Create new vendor settlement.
    """
    service = VendorSettlementService(uow)
    return await service.create_settlement(
        obj_in=settlement_in, organization_id=current_user.organization_id
    )

@router.get("", response_model=List[VendorSettlementListResponse])
async def read_vendor_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    uow: BaseUnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve vendor settlements.
    """
    service = VendorSettlementService(uow)
    return await service.get_multi(skip=skip, limit=limit)

@router.get("/{id}", response_model=VendorSettlementResponse)
async def read_vendor_settlement(
    *,
    uow: BaseUnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
    id: uuid.UUID,
) -> Any:
    """
    Get vendor settlement by ID.
    """
    service = VendorSettlementService(uow)
    return await service.get_by_id(settlement_id=id)

@router.patch("/{id}/status", response_model=VendorSettlementResponse)
async def update_vendor_settlement_status(
    *,
    uow: BaseUnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
    id: uuid.UUID,
    status_update: VendorSettlementStatusUpdate,
) -> Any:
    """
    Update vendor settlement status.
    """
    service = VendorSettlementService(uow)
    return await service.update_status(
        settlement_id=id, status=status_update.status
    )
