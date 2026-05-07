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
from app.services.uow import SQLAlchemyUnitOfWork

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_uow(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SQLAlchemyUnitOfWork, None]:
    """
    Provides a Unit of Work backed by the request-scoped DB session.

    Transaction contract:
      - The UoW context is entered here so __aexit__ is always guaranteed to run.
      - On success:   the service layer MUST call await uow.commit() explicitly.
      - On exception: __aexit__ rolls back automatically (safety-net).

    Session lifecycle is owned by get_db(), not this dependency.
    """
    uow = SQLAlchemyUnitOfWork(session=db)
    async with uow:
        yield uow

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
    
    # Tenant ID is mandatory on every access token in this multi-tenant system.
    # Absence means a misconfigured auth flow; fail closed rather than letting
    # require_tenant_id() raise TenantContextMissingError (RuntimeError → 500).
    if token_data.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    try:
        user_id = uuid.UUID(token_data.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    from app.repositories.user import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get(db, id=user_id)

    if not user:
        # Return 403 not 404: 404 lets a caller with a valid JWT enumerate
        # which user IDs exist inside the tenant.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # Defense-in-depth: the middleware already scopes the DB query to the JWT
    # tenant via the ContextVar, but we assert it explicitly so future refactors
    # cannot accidentally widen the lookup without breaking this invariant.
    if str(user.organization_id) != token_data.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_role(required_roles: list[str]):
    """
    Dependency to check if the current user has at least one of the required roles.

    RBAC is not yet wired. Until role-loading is implemented this raises 403 for
    every non-superuser, keeping every guarded route fail-closed.  When RBAC ships,
    replace the body with a real role-intersection check.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        # Fail closed: RBAC not yet implemented.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return role_checker
