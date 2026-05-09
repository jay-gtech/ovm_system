import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RiskAssessmentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    risk_score: int
    risk_level: str
    contributing_factors: Dict[str, Any]
    explanation_text: str
    generated_at: datetime
    source_snapshot_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskAssessmentListResponse(BaseModel):
    items: List[RiskAssessmentResponse]
    total: int
    skip: int
    limit: int


class RiskSummaryResponse(BaseModel):
    """Overview counts for the operational intelligence dashboard."""
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_assessed_entities: int
