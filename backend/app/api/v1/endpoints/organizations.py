from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.services.organization import OrganizationService
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
    TenantIsolationError,
    DomainError
)
from app.core.context import TenantContextMissingError

router = APIRouter()


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    obj_in: OrganizationCreate,
    current_user=Depends(deps.get_current_active_user),
):
    """
    Onboard a new organization (tenant).

    Security:
    - Requires an authenticated user. Authentication is validated via JWT.
    - TODO(rbac): Upgrade to `check_role(["superuser"])` once RBAC is wired.
      Until then, any authenticated user can trigger onboarding — acceptable
      only in early development; must be locked down before staging.
    - Slug enumeration is mitigated: 409 is only returned to authenticated callers.
    """
    service = OrganizationService(uow)
    try:
        return await service.create_organization(obj_in)
    except ConflictDomainError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except TenantContextMissingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user=Depends(deps.get_current_active_user)
):
    """
    Fetch the organization associated with the current authenticated session.
    Uses tenant context extracted from the JWT.
    """
    service = OrganizationService(uow)
    try:
        return await service.get_current_organization()
    except NotFoundDomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except TenantContextMissingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.patch("/{id}", response_model=OrganizationResponse)
async def update_organization(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    id: UUID,
    obj_in: OrganizationUpdate,
    current_user=Depends(deps.get_current_active_user)
):
    """
    Update organization details.

    Security:
    - Enforces tenant isolation: users can only update their own organization.
    - Fail-closed if organization ID does not match active tenant.
    - Slug is immutable and cannot be updated regardless of payload.
    """
    service = OrganizationService(uow)
    try:
        return await service.update_organization(id, obj_in)
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except NotFoundDomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except TenantContextMissingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
