import logging
from typing import Optional
from uuid import UUID

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import context, security

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant and user context from the authentication token.

    This middleware:
    1. Extracts the JWT from the Authorization header.
    2. Decodes the token to retrieve 'tenant_id' and 'sub' (user_id).
    3. Populates the request-scoped ContextVars.
    4. Attaches tenant_id and user_id to request.state for downstream access.
    5. Ensures context is reset in a finally block to prevent leakage.

    Fail-safety:
    If the token is missing, invalid, or lacks a tenant_id, the context
    variables remain None. Downstream repository calls that require
    a tenant (via require_tenant_id()) will fail-fast with a
    TenantContextMissingError.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        tenant_id: Optional[UUID] = None
        user_id: Optional[UUID] = None

        # 1. Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            try:
                # 2. Decode token
                payload = security.decode_token(token)
                
                # Extract user_id (sub)
                sub = payload.get("sub")
                if sub:
                    try:
                        user_id = UUID(str(sub))
                    except (ValueError, AttributeError):
                        logger.warning("Invalid user_id (sub) format in token: %.64r", sub)

                # Extract tenant_id
                tid = payload.get("tenant_id")
                if tid:
                    try:
                        tenant_id = UUID(str(tid))
                    except (ValueError, AttributeError):
                        logger.warning("Invalid tenant_id format in token: %.64r", tid)

            except JWTError:
                # Token is invalid; we don't raise here to allow public routes
                # and let the Authentication dependency handle 401/403.
                pass

        # 3. Bind to ContextVars
        tenant_token = context.set_tenant_id(tenant_id)
        user_token = context.set_user_id(user_id)

        # 4. Attach to request.state
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id

        try:
            return await call_next(request)
        finally:
            # 5. Guaranteed cleanup
            context.reset_tenant_id(tenant_token)
            context.reset_user_id(user_token)
