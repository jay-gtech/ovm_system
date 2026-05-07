from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.product import Product
from app.db.tenancy import apply_tenant_scope

class ProductRepository(BaseRepository[Product]):
    def __init__(self):
        super().__init__(Product)

    async def get_by_sku(self, db: AsyncSession, sku: str) -> Optional[Product]:
        """
        Fetch a single product by SKU with tenant isolation.
        """
        query = select(self.model).where(self.model.sku == sku)
        
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        query = apply_tenant_scope(query, self.model)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def count(self, db: AsyncSession) -> int:
        """
        Count total products for the current tenant.
        """
        query = select(func.count()).select_from(self.model)
        
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        query = apply_tenant_scope(query, self.model)
        
        result = await db.execute(query)
        return result.scalar() or 0
