from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern="^[a-z0-9-]+$")


class OrganizationCreate(OrganizationBase):
    """
    Schema for creating a new organization (tenant).
    """
    pass


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an existing organization.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """
    Schema for organization responses.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
