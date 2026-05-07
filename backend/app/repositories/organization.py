from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self):
        super().__init__(Organization)

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        """
        Fetch an organization by its unique slug.
        Used primarily during login/onboarding.
        """
        query = select(self.model).where(self.model.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()
