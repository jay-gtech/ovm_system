from contextvars import ContextVar, Token
from typing import Optional
from uuid import UUID

# ---------------------------------------------------------------------------
# Context variables for request-scoped storage.
# ContextVars are async-safe: each asyncio Task inherits a *copy* of the
# current context, so writes inside one request coroutine are never visible
# to sibling or parent coroutines.  Token-based reset guarantees that the
# variable is restored to its exact prior state even if the same ContextVar
# is nested (e.g. middleware → sub-middleware → dependency).
# ---------------------------------------------------------------------------

_tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)
_request_id_ctx: ContextVar[Optional[UUID]] = ContextVar("request_id", default=None)


class TenantContextMissingError(RuntimeError):
    """Raised when a tenant-scoped operation is attempted without an active tenant ID."""
    pass


# ---------------------------------------------------------------------------
# Tenant ID helpers
# ---------------------------------------------------------------------------

def get_tenant_id() -> Optional[UUID]:
    """Return the current tenant_id from the context, or None if not set."""
    return _tenant_id_ctx.get()


def set_tenant_id(tenant_id: Optional[UUID]) -> Token:
    """
    Set the current tenant_id in the context.

    Returns a Token that MUST be passed to reset_tenant_id() inside a
    finally block to prevent tenant leakage across requests.
    """
    return _tenant_id_ctx.set(tenant_id)


def reset_tenant_id(token: Token) -> None:
    """
    Reset the tenant_id context variable to the state captured by *token*.

    Always call this in a finally block after set_tenant_id().
    """
    _tenant_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# User ID helpers
# ---------------------------------------------------------------------------

def get_user_id() -> Optional[UUID]:
    """Return the current user_id from the context, or None if not set."""
    return _user_id_ctx.get()


def set_user_id(user_id: Optional[UUID]) -> Token:
    """
    Set the current user_id in the context.

    Returns a Token that MUST be passed to reset_user_id() inside a
    finally block.
    """
    return _user_id_ctx.set(user_id)


def reset_user_id(token: Token) -> None:
    """
    Reset the user_id context variable to the state captured by *token*.
    """
    _user_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# Request ID helpers
# ---------------------------------------------------------------------------

def get_request_id() -> Optional[UUID]:
    """Return the current request_id from the context, or None if not set."""
    return _request_id_ctx.get()


def set_request_id(request_id: Optional[UUID]) -> Token:
    """
    Set the current request_id in the context.

    Returns a Token that MUST be passed to reset_request_id() inside a
    finally block to ensure clean-up on every code path.
    """
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Token) -> None:
    """
    Reset the request_id context variable to the state captured by *token*.

    Always call this in a finally block after set_request_id().
    """
    _request_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# Fail-closed enforcement
# ---------------------------------------------------------------------------

def require_tenant_id() -> UUID:
    """
    Return the current tenant_id or raise TenantContextMissingError if not set.

    Use this inside repository methods to enforce that every database
    operation is tenant-scoped.  Raising is intentional (fail-closed):
    a missing tenant context is a programming error, not a user error.

    Future: this function is the natural insertion point for PostgreSQL
    RLS SET LOCAL calls once that layer is introduced.
    """
    tenant_id = _tenant_id_ctx.get()
    if tenant_id is None:
        raise TenantContextMissingError(
            "Tenant context is missing. All repository operations require "
            "an active tenant_id. Ensure TenantContextMiddleware has run "
            "before any DB access."
        )
    return tenant_id


# ---------------------------------------------------------------------------
# Composite clear — useful for background-task bootstrap and test teardown
# ---------------------------------------------------------------------------

def clear_context() -> None:
    """
    Hard-reset both context variables to None without a token.

    Intended for:
      - Background-task entry points (Celery tasks, Redis Streams consumers)
        that create a *fresh* asyncio context and must not inherit any stale
        tenant from the parent scope.
      - Test teardown to prevent inter-test leakage.

    Do NOT use this inside normal request middleware — prefer the token-based
    reset_tenant_id / reset_request_id pattern instead.
    """
    _tenant_id_ctx.set(None)
    _user_id_ctx.set(None)
    _request_id_ctx.set(None)
