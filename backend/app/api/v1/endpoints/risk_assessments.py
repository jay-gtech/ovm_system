import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.repositories.risk_assessment import RiskAssessmentRepository
from app.schemas.risk_assessment import (
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    RiskSummaryResponse,
)

router = APIRouter()

_ALLOWED_ROLES = ["ADMIN", "MANAGER", "ACCOUNTS"]


# ---------------------------------------------------------------------------
# Summary endpoint — must come before /{id} to avoid path-parameter collision
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Return risk level counts based on each entity's LATEST assessment.

    Used by the operational intelligence dashboard summary cards.
    One efficient SQL query with a max-per-entity subquery.
    """
    repo = RiskAssessmentRepository()
    counts = await repo.get_risk_summary(db)
    total = sum(counts.values())
    return RiskSummaryResponse(
        critical_count=counts.get("CRITICAL", 0),
        high_count=counts.get("HIGH", 0),
        medium_count=counts.get("MEDIUM", 0),
        low_count=counts.get("LOW", 0),
        total_assessed_entities=total,
    )


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

@router.get("", response_model=RiskAssessmentListResponse)
async def list_risk_assessments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    entity_type: Optional[str] = Query(default=None, description="invoice | vendor | payment"),
    entity_id: Optional[uuid.UUID] = Query(default=None),
    risk_level: Optional[str] = Query(
        default=None, description="LOW | MEDIUM | HIGH | CRITICAL"
    ),
    generated_after: Optional[datetime] = Query(default=None),
    generated_before: Optional[datetime] = Query(default=None),
    latest_only: bool = Query(
        default=False,
        description="Return only the most recent assessment per entity",
    ),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    List risk assessments for the current tenant.

    Supports:
    - Pagination (skip / limit)
    - Entity type and ID filtering
    - Risk level filtering (LOW | MEDIUM | HIGH | CRITICAL)
    - Date range filtering (generated_after / generated_before)
    - latest_only=true  → one assessment per entity (dashboard mode)
    """
    repo = RiskAssessmentRepository()
    filters = dict(
        entity_type=entity_type,
        entity_id=entity_id,
        risk_level=risk_level,
        generated_after=generated_after,
        generated_before=generated_before,
        latest_only=latest_only,
    )
    items = await repo.get_multi(db, skip=skip, limit=limit, **filters)
    total = await repo.count(db, **filters)
    return RiskAssessmentListResponse(
        items=list(items), total=total, skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# Entity history endpoint
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_type}/{entity_id}", response_model=RiskAssessmentListResponse)
async def list_entity_risk_history(
    entity_type: str,
    entity_id: uuid.UUID,
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """
    Return historical risk assessments for a specific entity, oldest-first.

    Used to render the risk trend timeline for an entity.
    Returns up to `limit` records ordered by generated_at ascending.
    """
    repo = RiskAssessmentRepository()
    items = await repo.get_entity_history(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    return RiskAssessmentListResponse(
        items=list(items), total=len(items), skip=0, limit=limit
    )


# ---------------------------------------------------------------------------
# Single-record endpoint — must come AFTER /summary and /entity/... routes
# ---------------------------------------------------------------------------

@router.get("/{assessment_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.check_role(_ALLOWED_ROLES)),
):
    """Retrieve a single risk assessment by ID (tenant-scoped)."""
    repo = RiskAssessmentRepository()
    assessment = await repo.get(db, assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk assessment not found.",
        )
    return assessment
