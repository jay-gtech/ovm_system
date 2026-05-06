from typing import Type, TypeVar
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.context import require_tenant_id

T = TypeVar("T")


def apply_tenant_scope(query: Select[T], model: Type[T]) -> Select[T]:
    """
    Apply a tenant filter to an SQLAlchemy select statement.

    This helper ensures that every query against a tenant-aware model
    is filtered by the current organization_id.

    Args:
        query: The SQLAlchemy select statement.
        model: The SQLAlchemy model class (must have organization_id).

    Returns:
        The filtered select statement.

    Raises:
        TenantContextMissingError: If no tenant_id is set in the context.
    """
    tenant_id = require_tenant_id()
    
    # Check if the model has organization_id column
    if hasattr(model, "organization_id"):
        return query.where(model.organization_id == tenant_id)
    
    return query


async def set_rls_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """
    Prepare the database session for Row Level Security (RLS).

    This is a placeholder for future PostgreSQL RLS implementation.
    It will eventually execute:
    SET LOCAL app.current_tenant = :tenant_id;

    Args:
        session: The active database session.
        tenant_id: The tenant ID to set for the session.
    """
    # Placeholder: In a real RLS implementation, we would set a session variable.
    # For now, we just ensure the session is aware of the tenant.
    # await session.execute(text("SET LOCAL app.current_tenant = :tid"), {"tid": str(tenant_id)})
    pass
