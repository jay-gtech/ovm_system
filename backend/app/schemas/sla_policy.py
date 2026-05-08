import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class SLAPolicyCreate(BaseModel):
    alert_type: str = Field(..., max_length=50)
    is_active: bool = True
    acknowledgement_minutes: int = Field(default=60, ge=1)
    resolution_minutes: int = Field(default=480, ge=1)
    escalation_level_1_minutes: int = Field(default=120, ge=1)
    escalation_level_2_minutes: int = Field(default=360, ge=1)


class SLAPolicyUpdate(BaseModel):
    is_active: Optional[bool] = None
    acknowledgement_minutes: Optional[int] = Field(default=None, ge=1)
    resolution_minutes: Optional[int] = Field(default=None, ge=1)
    escalation_level_1_minutes: Optional[int] = Field(default=None, ge=1)
    escalation_level_2_minutes: Optional[int] = Field(default=None, ge=1)


class SLAPolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    alert_type: str
    is_active: bool
    acknowledgement_minutes: int
    resolution_minutes: int
    escalation_level_1_minutes: int
    escalation_level_2_minutes: int

    model_config = {"from_attributes": True}


class SLAPolicyListResponse(BaseModel):
    items: List[SLAPolicyResponse]
    total: int
