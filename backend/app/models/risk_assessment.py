import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import String, Integer, Text, UUID, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import TenantBaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskEntityType(str, Enum):
    INVOICE = "invoice"
    VENDOR = "vendor"
    PAYMENT = "payment"


class RiskAssessment(TenantBaseModel):
    """
    Append-only operational risk assessment record.

    Design invariants:
    - Never updated after creation — historical records are permanent.
    - No soft-delete: risk history must be preserved for trend analysis.
    - Multiple assessments per entity form a time-series risk trend.
    - Tenant-isolated via organization_id (TenantBaseModel).

    Query patterns:
    - Latest score:  WHERE entity=X ORDER BY generated_at DESC LIMIT 1
    - Trend:         WHERE entity=X ORDER BY generated_at ASC
    - Dashboard:     join to max-per-entity subquery, filter by risk_level
    """

    __table_args__ = (
        # Primary entity lookup — supports latest-score queries and history browsing.
        Index(
            "ix_risk_entity_time",
            "organization_id", "entity_type", "entity_id", "generated_at",
        ),
        # Risk-level dashboard filter — "show all CRITICAL entities" pattern.
        Index(
            "ix_risk_level_time",
            "organization_id", "risk_level", "generated_at",
        ),
    )

    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    contributing_factors: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    source_snapshot_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment(entity={self.entity_type}:{self.entity_id}, "
            f"score={self.risk_score}, level={self.risk_level})>"
        )
