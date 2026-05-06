from typing import Any, Generic, Type, TypeVar, Optional, Sequence
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base
from app.db.tenancy import apply_tenant_scope
from app.core.context import require_tenant_id

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base repository with common async CRUD operations.
        Includes production-safe tenant isolation and soft-delete support.
        """
        self.model = model

    async def get(
        self, db: AsyncSession, id: uuid.UUID
    ) -> Optional[ModelType]:
        """
        Fetch a single record by ID with automatic tenant isolation.
        """
        query = select(self.model).where(self.model.id == id)
        
        # Apply soft-delete filter if supported by model
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        # Apply tenant isolation if model is tenant-aware
        if hasattr(self.model, "organization_id"):
            query = apply_tenant_scope(query, self.model)
            
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[ModelType]:
        """
        Fetch multiple records with pagination and automatic tenant isolation.
        """
        query = select(self.model).offset(skip).limit(limit)
        
        # Apply soft-delete filter if supported by model
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        # Apply tenant isolation if model is tenant-aware
        if hasattr(self.model, "organization_id"):
            query = apply_tenant_scope(query, self.model)
            
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> ModelType:
        """
        Create a new record.

        For tenant-aware models (those with organization_id):
          - If organization_id is absent from obj_in, it is injected automatically
            from the active tenant context (fail-closed via require_tenant_id).
          - If organization_id is present but does not match the active tenant,
            a ValueError is raised — cross-tenant writes are never silently allowed.
        """
        if hasattr(self.model, "organization_id"):
            tenant_id = require_tenant_id()  # raises TenantContextMissingError if missing
            supplied = obj_in.get("organization_id")
            if supplied is None:
                # Auto-inject to prevent callers from forgetting to set it
                obj_in = {**obj_in, "organization_id": tenant_id}
            elif supplied != tenant_id:
                raise ValueError(
                    f"Cross-tenant write rejected: supplied organization_id "
                    f"{supplied!r} does not match active tenant {tenant_id!r}."
                )
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict
    ) -> ModelType:
        """
        Update an existing record.

        Prevents cross-tenant mutation: if obj_in contains organization_id and
        the value does not match the active tenant context, a ValueError is raised.
        This guards against a service-layer bug silently re-assigning a record
        to a different tenant.
        """
        if hasattr(db_obj, "organization_id") and "organization_id" in obj_in:
            tenant_id = require_tenant_id()
            if obj_in["organization_id"] != tenant_id:
                raise ValueError(
                    "Cross-tenant update rejected: cannot reassign organization_id "
                    f"from {getattr(db_obj, 'organization_id')!r} to "
                    f"{obj_in['organization_id']!r} (active tenant: {tenant_id!r})."
                )
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self, db: AsyncSession, *, id: uuid.UUID
    ) -> Optional[ModelType]:
        """
        Remove a record. Enforces soft-delete if supported by the model.
        Financial entities are never hard-deleted if they support SoftDeleteMixin.
        """
        obj = await self.get(db, id)
        if obj:
            if hasattr(obj, "is_deleted"):
                # Production safety: Soft-delete instead of hard-delete
                obj.is_deleted = True
                if hasattr(obj, "deleted_at"):
                    obj.deleted_at = datetime.now(timezone.utc)
                db.add(obj)
                await db.flush()
                # Soft-delete flushed into the active transaction. Refresh to
                # capture server-side defaults (deleted_at, updated_at).
                # Commit is deferred to the service layer via UoW.
                await db.refresh(obj)
            else:
                # Fallback to hard-delete for non-financial/non-soft-delete models
                await db.delete(obj)
                await db.flush()
        return obj
