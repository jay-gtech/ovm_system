import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError

from app.api import deps
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorListResponse,
    VendorStatusUpdate
)
from app.services.vendor import VendorService
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
    ValidationDomainError
)

router = APIRouter()

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    obj_in: VendorCreate,
    current_user = Depends(deps.get_current_active_user),
):
    """
    Create a new vendor.

    Security:
    - Scoped to the current tenant.
    - Ensures vendor_code uniqueness within the tenant.
    """
    service = VendorService(uow)
    try:
        return await service.create_vendor(obj_in)
    except ConflictDomainError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationDomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except IntegrityError:
        # Last-resort safety net: if IntegrityError somehow escapes the service
        # layer (e.g. under extreme concurrency), never surface raw DB exceptions.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor with this code already exists.",
        )

@router.get("/", response_model=VendorListResponse)
async def list_vendors(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(deps.get_current_active_user),
):
    """
    List vendors for the current tenant with accurate pagination.
    """
    service = VendorService(uow)
    vendors, total = await service.list_vendors(skip=skip, limit=limit)
    return {"items": vendors, "total": total}

@router.get("/{id}", response_model=VendorResponse)
async def get_vendor(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    id: uuid.UUID,
    current_user = Depends(deps.get_current_active_user),
):
    """
    Fetch a specific vendor by ID.
    """
    service = VendorService(uow)
    try:
        return await service.get_vendor(id)
    except NotFoundDomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

@router.patch("/{id}", response_model=VendorResponse)
async def update_vendor(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    id: uuid.UUID,
    obj_in: VendorUpdate,
    current_user = Depends(deps.get_current_active_user),
):
    """
    Update vendor details.
    
    Rule: vendor_code is immutable and will be ignored if provided.
    """
    service = VendorService(uow)
    try:
        return await service.update_vendor(id, obj_in)
    except NotFoundDomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationDomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

@router.patch("/{id}/status", response_model=VendorResponse)
async def update_vendor_status(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    id: uuid.UUID,
    obj_in: VendorStatusUpdate,
    current_user = Depends(deps.get_current_active_user),
):
    """
    Update vendor status (e.g., ACTIVE -> SUSPENDED).
    """
    service = VendorService(uow)
    try:
        return await service.update_status(id, obj_in)
    except NotFoundDomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
