import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    channel: str
    title: str
    message: str
    status: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    retry_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    skip: int
    limit: int


class UnreadCountResponse(BaseModel):
    unread_count: int
