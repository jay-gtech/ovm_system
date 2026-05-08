import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api import deps
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogListResponse
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

_audit_repo = AuditRepository()


def _require_audit_access(current_user: User = Depends(deps.get_current_active_user)) -> User:
    """
    RBAC gate for audit endpoints.
    Permits: superusers and users whose role includes ADMIN, MANAGER, or ACCOUNTS.
    Until the full RBAC role-load pipeline ships, superuser flag is used as the
    trusted path; role-string check guards the non-superuser path.
    """
    if current_user.is_superuser:
        return current_user
    # When role loading is wired, check loaded roles here.
    # For now fail closed — audit data is highly sensitive.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Audit access requires ADMIN, MANAGER, or ACCOUNTS role.",
    )


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=AuditLogListResponse,
    summary="Get paginated audit trail for a specific entity",
)
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    _: User = Depends(_require_audit_access),
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
) -> AuditLogListResponse:
    """
    Return the chronological audit trail for a single entity (invoice, payment, etc.).

    - Tenant-scoped: only returns records for the authenticated tenant.
    - Immutable: no write operations exposed on this resource.
    - Paginated via skip/limit with accurate total count.
    """
    items = await _audit_repo.get_by_entity(
        uow.session, entity_type, entity_id, skip=skip, limit=limit
    )
    total = await _audit_repo.count_by_entity(uow.session, entity_type, entity_id)
    return AuditLogListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.get(
    "/search",
    response_model=AuditLogListResponse,
    summary="Search audit logs with optional filters",
)
async def search_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    actor_user_id: Optional[uuid.UUID] = Query(None, description="Filter by actor user ID"),
    date_from: Optional[str] = Query(None, description="ISO 8601 start timestamp (inclusive)"),
    date_to: Optional[str] = Query(None, description="ISO 8601 end timestamp (inclusive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: User = Depends(_require_audit_access),
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
) -> AuditLogListResponse:
    """
    Search across all audit logs for the authenticated tenant.

    Filters are optional and combinable. Results are sorted newest-first.
    Total reflects the full matched count, not just the current page.
    """
    items = await _audit_repo.search(
        uow.session,
        entity_type=entity_type,
        action=action,
        actor_user_id=actor_user_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    total = await _audit_repo.search_count(
        uow.session,
        entity_type=entity_type,
        action=action,
        actor_user_id=actor_user_id,
        date_from=date_from,
        date_to=date_to,
    )
    return AuditLogListResponse(items=list(items), total=total, skip=skip, limit=limit)
