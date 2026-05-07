from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, reusable_oauth2
from app.core import security
from app.core.redis_client import blacklist_token, is_token_blacklisted
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RefreshTokenRequest
from app.schemas.token import LoginResponse, Token, TokenPayload, UserSummary

router = APIRouter()

_user_repo = UserRepository()

_invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/login", response_model=LoginResponse)
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    login_in: LoginRequest,
) -> Any:
    """
    Authenticate a user and return access + refresh tokens with a user summary.

    Tenant identification: the organization_slug in the request body determines
    which tenant to authenticate against. Because email uniqueness is scoped per
    organization, the slug is required to locate the correct user record.

    This endpoint is intentionally public — no auth dependency.
    """
    # Cross-tenant lookup: joins Organization on slug, applies active/deleted
    # filters, and eagerly loads roles. Does NOT use apply_tenant_scope.
    user = await _user_repo.get_by_email_and_org_slug(
        db,
        email=login_in.email,
        org_slug=login_in.organization_slug,
    )

    # Use the same error for "org not found", "user not found", and "wrong
    # password" to prevent enumeration of org slugs and email addresses.
    if user is None:
        raise _invalid_credentials

    if not security.verify_password(login_in.password, user.hashed_password):
        raise _invalid_credentials

    # Stamp last login time. Direct ORM mutation is intentional here: this
    # endpoint cannot use the tenant-scoped UoW (no JWT → no ContextVar).
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()

    # Collect tenant-scoped role names. The relationship was eagerly loaded in
    # get_by_email_and_org_slug. Empty list is correct until RBAC is wired.
    roles: list[str] = [r.name for r in user.roles]

    access_token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
        roles=roles,
    )
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=user.organization_id,
            is_superuser=user.is_superuser,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(reusable_oauth2),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Invalidate the current access token.

    The get_current_active_user dependency validates the token before this
    handler runs. We decode a second time only to extract jti and exp —
    both are guaranteed present at this point.
    """
    try:
        payload = security.decode_token(token)
    except JWTError:
        # Already invalid; nothing to blacklist. Treat as success.
        return

    jti: str | None = payload.get("jti")
    exp: int | None = payload.get("exp")

    if jti and exp:
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            await blacklist_token(jti, ttl)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_in: RefreshTokenRequest,
) -> Any:
    """
    Issue a new access token from a valid refresh token.

    No rotation: the refresh token itself is not replaced. The refresh token
    is checked against the Redis blacklist so that logout invalidates both
    the access token (blacklisted in /logout) and, eventually, the refresh
    token if a /logout-all endpoint is added.
    """
    invalid_refresh = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security.decode_token(refresh_in.refresh_token)
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise invalid_refresh

    # Token-type check: only refresh tokens may be used here.
    if token_data.type != "refresh":
        raise invalid_refresh

    if not token_data.sub or not token_data.jti or not token_data.tenant_id:
        raise invalid_refresh

    # Blacklist check: covers revoked refresh tokens (e.g. after a logout-all).
    if await is_token_blacklisted(token_data.jti):
        raise invalid_refresh

    new_access_token = security.create_access_token(
        subject=token_data.sub,
        tenant_id=token_data.tenant_id,
        roles=token_data.roles,
    )

    return Token(
        access_token=new_access_token,
        refresh_token=refresh_in.refresh_token,
    )
