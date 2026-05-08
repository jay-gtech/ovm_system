import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.audit_log import AuditAction
from app.models.user import User
from app.repositories.sla_policy import SLAPolicyRepository
from app.schemas.sla_policy import (
    SLAPolicyCreate,
    SLAPolicyListResponse,
    SLAPolicyResponse,
    SLAPolicyUpdate,
)
from app.services.audit import AuditService
from app.services.uow import SQLAlchemyUnitOfWork
from app.core.context import require_tenant_id

router = APIRouter()

_ALLOWED_ROLES = ["ADMIN", "MANAGER", "ACCOUNTS"]


@router.get("", response_model=SLAPolicyListResponse)
async def list_sla_policies(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """List all SLA policies for the current tenant."""
    repo = SLAPolicyRepository()
    items = await repo.list_for_tenant(db)
    return SLAPolicyListResponse(items=list(items), total=len(items))


@router.post("", response_model=SLAPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    data: SLAPolicyCreate,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Create a new SLA policy for the given alert_type.

    Returns 409 if an SLA policy for that alert_type already exists in this tenant.
    """
    tenant_id = require_tenant_id()
    repo = SLAPolicyRepository()
    try:
        policy = await repo.create(uow.session, obj_in={
            "organization_id": tenant_id,
            **data.model_dump(),
        })
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SLA policy for alert_type '{data.alert_type}' already exists.",
        )
    await AuditService.log_event(
        uow.session,
        entity_type="sla_policy",
        entity_id=policy.id,
        action=AuditAction.SLA_POLICY_CREATED,
        actor_user_id=current_user.id,
    )
    await uow.commit()
    return policy


@router.patch("/{policy_id}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    policy_id: uuid.UUID,
    data: SLAPolicyUpdate,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """Update an existing SLA policy (partial update — only supplied fields change)."""
    repo = SLAPolicyRepository()
    policy = await repo.get(uow.session, policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found.",
        )
    changes = data.model_dump(exclude_none=True)
    if not changes:
        return policy
    updated = await repo.update(uow.session, db_obj=policy, obj_in=changes)
    await AuditService.log_event(
        uow.session,
        entity_type="sla_policy",
        entity_id=policy_id,
        action=AuditAction.SLA_POLICY_UPDATED,
        actor_user_id=current_user.id,
    )
    await uow.commit()
    return updated
