from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.user import User
from app.db.tenancy import apply_tenant_scope


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Fetch a user by email within the current tenant scope.
        """
        query = select(self.model).where(self.model.email == email)
        # apply_tenant_scope is applied here to ensure we only find the user 
        # within the organization active in the current request context.
        query = apply_tenant_scope(query, self.model)
        result = await db.execute(query)
        return result.scalar_one_or_none()
