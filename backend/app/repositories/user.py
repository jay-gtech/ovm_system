from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.user import User
from app.models.organization import Organization
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

    async def get_by_email_and_org_slug(
        self, db: AsyncSession, *, email: str, org_slug: str
    ) -> Optional[User]:
        """
        Cross-tenant lookup used exclusively during authentication.

        Intentionally bypasses tenant scope: at login time no JWT exists, so
        no tenant ContextVar is set and apply_tenant_scope would raise
        TenantContextMissingError. The tenant boundary is enforced here by
        joining on Organization.slug instead.

        Filters: active user, active organization, not soft-deleted.
        Eagerly loads roles so the caller can include them in the JWT without
        triggering a lazy-load inside a closed async context.
        """
        query = (
            select(self.model)
            .join(Organization, self.model.organization_id == Organization.id)
            .where(self.model.email == email)
            .where(Organization.slug == org_slug)
            .where(Organization.is_active.is_(True))
            .where(self.model.is_active.is_(True))
            .where(self.model.is_deleted.is_(False))
            .options(selectinload(User.roles))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
