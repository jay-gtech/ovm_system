from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    organization_slug: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
