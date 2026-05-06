import uuid
from typing import AsyncGenerator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.core.redis_client import is_token_blacklisted

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = security.decode_token(token)
        token_data = TokenPayload(**payload)

        # --- Token-type confusion prevention ---
        # Refresh tokens MUST NOT be accepted by protected resource endpoints.
        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type",
            )

        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        # jti is required for blacklist checks; treat absence as invalid.
        if token_data.jti is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        if await is_token_blacklisted(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # TODO(auth): Replace this placeholder before ANY production deployment.
    # WARNING: This stub bypasses real identity resolution. Every route protected
    # by this dependency currently accepts any valid, non-revoked JWT and returns
    # a fake user object. Real user lookup must be wired here (see commented block
    # below) once the user CRUD layer is complete.
    #
    # Real implementation:
    #   user = await crud.user.get(db, id=token_data.sub)
    #   if not user:
    #       raise HTTPException(status_code=404, detail="User not found")
    #   return user
    user_id = uuid.UUID(token_data.sub)
    return User(
        id=user_id,
        email="placeholder@example.com",
        is_active=True,
        is_superuser=False
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_role(roles: list[str]):
    """
    Placeholder for role dependency.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Placeholder logic
        # user_roles = [r.name for r in current_user.roles]
        # if not any(role in user_roles for role in roles):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="The user doesn't have enough privileges",
        #     )
        return current_user
    return role_checker
