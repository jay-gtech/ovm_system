import uuid
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    jti: Optional[str] = None
    type: Optional[Literal["access", "refresh"]] = None
    tenant_id: Optional[str] = None
    roles: list[str] = Field(default_factory=list)


class UserSummary(BaseModel):
    """Minimal user representation returned with the login response."""
    id: uuid.UUID
    email: str
    full_name: str
    organization_id: uuid.UUID
    is_superuser: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSummary
