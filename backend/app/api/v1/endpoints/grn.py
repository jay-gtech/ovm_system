import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.models.user import User
from app.schemas.grn import (
    GRNCreate,
    GRNResponse,
    GRNListResponse,
)
from app.services.grn import GRNService, GRNServiceError
from app.services.uow import SQLAlchemyUnitOfWork
from app.core.context import require_tenant_id

router = APIRouter()

def get_grn_service(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow)
) -> GRNService:
    return GRNService(uow)

@router.post(
    "",
    response_model=GRNResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_grn(
    *,
    service: GRNService = Depends(get_grn_service),
    current_user: User = Depends(deps.get_current_active_user),
    data: GRNCreate
):
    """
    Create a new GRN against a specific Purchase Order.
    """
    tenant_id = require_tenant_id()
    try:
        return await service.create_grn(
            organization_id=tenant_id,
            user_id=current_user.id,
            grn_in=data
        )
    except GRNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id}", response_model=GRNResponse)
async def get_grn(
    id: uuid.UUID,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get a specific GRN with line items."""
    tenant_id = require_tenant_id()
    async with uow:
        grn = await uow.grns.get_with_items(uow.session, tenant_id, id)
        if not grn:
            raise HTTPException(status_code=404, detail="GRN not found")
        return grn

@router.get("/po/{po_id}", response_model=List[GRNListResponse])
async def list_grns_by_po(
    po_id: uuid.UUID,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all GRNs for a specific Purchase Order."""
    tenant_id = require_tenant_id()
    async with uow:
        grns = await uow.grns.list_by_po_id(uow.session, tenant_id, po_id)
        return grns

@router.post("/{id}/complete", response_model=GRNResponse)
async def complete_grn(
    id: uuid.UUID,
    service: GRNService = Depends(get_grn_service),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Mark a GRN as completed."""
    tenant_id = require_tenant_id()
    try:
        return await service.complete_receipt(
            organization_id=tenant_id,
            user_id=current_user.id,
            grn_id=id
        )
    except GRNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
