from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.vendor import Vendor
from app.db.tenancy import apply_tenant_scope

class VendorRepository(BaseRepository[Vendor]):
    def __init__(self):
        """
        Repository for Vendor entity. 
        Inherits tenant-isolation and soft-delete logic from BaseRepository.
        """
        super().__init__(Vendor)

    async def get_by_code(self, db: AsyncSession, *, vendor_code: str) -> Optional[Vendor]:
        """
        Fetch a single vendor by vendor_code.
        Enforces tenant isolation and soft-delete filtering.
        """
        query = select(self.model).where(self.model.vendor_code == vendor_code)

        # BaseRepository handles these in get/get_multi,
        # but for custom queries we apply them manually.
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        if hasattr(self.model, "organization_id"):
            query = apply_tenant_scope(query, self.model)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def count(self, db: AsyncSession) -> int:
        """
        Return the total count of active (non-deleted) vendors for the current tenant.
        Applies the same tenant-scope and soft-delete guards as get_multi so that
        the list endpoint can return an accurate DB-level total, not len(page).
        """
        query = select(func.count()).select_from(self.model)

        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        if hasattr(self.model, "organization_id"):
            query = apply_tenant_scope(query, self.model)

        result = await db.execute(query)
        return result.scalar_one()
