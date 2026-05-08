import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    alert_type: str
    severity: str
    entity_type: str
    entity_id: uuid.UUID
    title: str
    message: str
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by_user_id: Optional[uuid.UUID] = None
    resolved_by_user_id: Optional[uuid.UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    skip: int
    limit: int


class BulkAcknowledgeRequest(BaseModel):
    """
    Optional filters for bulk acknowledgment.

    All matching OPEN alerts for the current tenant (scoped by JWT) are
    transitioned to ACKNOWLEDGED in a single transaction.  Omit a filter
    field to match all values of that dimension.
    """
    severity: Optional[str] = Field(default=None, description="CRITICAL | HIGH | MEDIUM | LOW")
    alert_type: Optional[str] = Field(default=None)


class BulkAcknowledgeResponse(BaseModel):
    acknowledged_count: int
