import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    BulkAcknowledgeRequest,
    BulkAcknowledgeResponse,
)
from app.services.alert import AlertService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

_ALLOWED_ROLES = ["ADMIN", "MANAGER", "ACCOUNTS"]


# ---------------------------------------------------------------------------
# Read endpoints — use bare AsyncSession (no writes, no commit needed)
# ---------------------------------------------------------------------------

@router.get("", response_model=AlertListResponse)
async def list_alerts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = Query(default=None, description="OPEN | ACKNOWLEDGED | RESOLVED"),
    severity: Optional[str] = Query(default=None, description="CRITICAL | HIGH | MEDIUM | LOW"),
    alert_type: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[uuid.UUID] = Query(default=None),
    triggered_after: Optional[datetime] = Query(default=None),
    triggered_before: Optional[datetime] = Query(default=None),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    List operational alerts for the current tenant.

    Supports filtering by severity, status, alert_type, entity, and date range.
    Results are ordered by triggered_at descending (most recent first).
    """
    repo = AlertRepository()
    filters = dict(
        status=status,
        severity=severity,
        alert_type=alert_type,
        entity_type=entity_type,
        entity_id=entity_id,
        triggered_after=triggered_after,
        triggered_before=triggered_before,
    )
    items = await repo.get_multi(db, skip=skip, limit=limit, **filters)
    total = await repo.count(db, **filters)
    return AlertListResponse(items=list(items), total=total, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """Retrieve a single alert by ID (tenant-scoped)."""
    repo = AlertRepository()
    alert = await repo.get(db, alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )
    return alert


# ---------------------------------------------------------------------------
# Write endpoints — use UoW so commit is explicit and rollback-safe
# ---------------------------------------------------------------------------

@router.post("/bulk-acknowledge", response_model=BulkAcknowledgeResponse)
async def bulk_acknowledge_alerts(
    body: BulkAcknowledgeRequest,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Acknowledge ALL OPEN alerts for the current tenant in one transaction.

    Safer than N individual PATCH calls from the UI:
      - Tenant-scoped: only this JWT tenant's alerts are touched.
      - Pagination-independent: all matching OPEN alerts, not just current page.
      - Single transaction: atomic — either all succeed or none.
      - Optional filters: narrow by severity and/or alert_type.

    Returns the count of alerts transitioned.
    """
    svc = AlertService(db=uow.session)
    count = await svc.bulk_acknowledge(
        user_id=current_user.id,
        severity=body.severity,
        alert_type=body.alert_type,
    )
    await uow.commit()
    return BulkAcknowledgeResponse(acknowledged_count=count)


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Transition an OPEN alert to ACKNOWLEDGED.

    Returns 400 if the alert is already ACKNOWLEDGED or RESOLVED.
    Returns 404 if the alert does not exist in the current tenant.
    """
    svc = AlertService(db=uow.session)
    try:
        alert = await svc.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await uow.commit()
    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: uuid.UUID,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Transition an OPEN or ACKNOWLEDGED alert to RESOLVED (terminal state).

    Returns 400 if the alert is already RESOLVED.
    Returns 404 if the alert does not exist in the current tenant.
    """
    svc = AlertService(db=uow.session)
    try:
        alert = await svc.resolve_alert(
            alert_id=alert_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await uow.commit()
    return alert
