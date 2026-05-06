from typing import Any, Generic, Type, TypeVar, Optional, Sequence
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base repository with common async CRUD operations.
        Includes production-safe tenant isolation and soft-delete support.
        """
        self.model = model

    async def get(
        self, db: AsyncSession, id: uuid.UUID, *, organization_id: Optional[uuid.UUID] = None
    ) -> Optional[ModelType]:
        """
        Fetch a single record by ID with optional tenant isolation and soft-delete check.
        """
        query = select(self.model).where(self.model.id == id)
        
        # Apply soft-delete filter if supported by model
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        # Apply tenant isolation if organization_id is provided
        if organization_id is not None:
            if not hasattr(self.model, "organization_id"):
                raise ValueError(f"Model {self.model.__name__} lacks tenant support (organization_id)")
            query = query.where(self.model.organization_id == organization_id)
            
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        organization_id: Optional[uuid.UUID] = None
    ) -> Sequence[ModelType]:
        """
        Fetch multiple records with pagination, tenant isolation, and soft-delete filtering.
        """
        query = select(self.model).offset(skip).limit(limit)
        
        # Apply soft-delete filter if supported by model
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        # Apply tenant isolation if organization_id is provided
        if organization_id is not None:
            if not hasattr(self.model, "organization_id"):
                raise ValueError(f"Model {self.model.__name__} lacks tenant support (organization_id)")
            query = query.where(self.model.organization_id == organization_id)
            
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict
    ) -> ModelType:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self, db: AsyncSession, *, id: uuid.UUID, organization_id: Optional[uuid.UUID] = None
    ) -> Optional[ModelType]:
        """
        Remove a record. Enforces soft-delete if supported by the model.
        Financial entities are never hard-deleted if they support SoftDeleteMixin.
        """
        obj = await self.get(db, id, organization_id=organization_id)
        if obj:
            if hasattr(obj, "is_deleted"):
                # Production safety: Soft-delete instead of hard-delete
                obj.is_deleted = True
                if hasattr(obj, "deleted_at"):
                    obj.deleted_at = datetime.now(timezone.utc)
                db.add(obj)
                await db.commit()
                # Refresh to ensure ORM state reflects the committed soft-delete
                await db.refresh(obj)
            else:
                # Fallback to hard-delete for non-financial/non-soft-delete models
                await db.delete(obj)
                await db.commit()
        return obj
