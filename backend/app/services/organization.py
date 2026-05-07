from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.services.base import BaseService
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
    TenantIsolationError
)
from app.core.context import require_tenant_id


class OrganizationService(BaseService):
    """
    Service for managing Organization (Tenant) lifecycle.
    """

    async def create_organization(self, obj_in: OrganizationCreate) -> Organization:
        """
        Create a new organization (onboarding).

        Financial rule: Slugs must be unique and immutable once used in transactions.

        The optimistic check below is a fast-path UX guard. The authoritative
        uniqueness gate is the DB UNIQUE constraint on slug. Any TOCTOU race
        between the check and the insert is caught by the IntegrityError handler,
        which rolls back and surfaces a clean ConflictDomainError.
        """
        existing = await self.uow.organizations.get_by_slug(self.uow.session, obj_in.slug)
        if existing:
            raise ConflictDomainError(
                f"Organization with slug '{obj_in.slug}' already exists."
            )

        try:
            org = await self.uow.organizations.create(
                self.uow.session,
                obj_in=obj_in.model_dump()
            )
        except IntegrityError:
            # TOCTOU: a concurrent request won the race on the unique slug
            # constraint. Roll back the failed flush and surface as a clean
            # conflict error — never let DB internals reach the HTTP layer.
            await self.uow.rollback()
            raise ConflictDomainError(
                f"Organization with slug '{obj_in.slug}' already exists."
            )

        # Record audit with the new org.id as the bootstrap tenant reference.
        # tenant_id context does not exist yet at bootstrap time; metadata
        # carries the new tenant identity for future DB-backed audit hooks.
        await self.record_audit(
            action="create",
            resource_type="organization",
            resource_id=str(org.id),
            payload=obj_in.model_dump(),
            metadata={"bootstrap_tenant_id": str(org.id)}
        )

        await self.uow.commit()
        return org

    async def get_current_organization(self) -> Organization:
        """
        Fetch the current organization based on tenant context.
        """
        tenant_id = require_tenant_id()
        org = await self.uow.organizations.get(self.uow.session, tenant_id)
        if not org:
            raise NotFoundDomainError(f"Organization '{tenant_id}' not found.")
        return org

    async def update_organization(self, org_id: UUID, obj_in: OrganizationUpdate) -> Organization:
        """
        Update organization details. Enforces tenant isolation.
        """
        tenant_id = require_tenant_id()

        # Security: Fail-closed if trying to update another organization.
        # Authorization check happens BEFORE any DB read — correct order.
        if org_id != tenant_id:
            raise TenantIsolationError("Cannot update another organization.")

        org = await self.uow.organizations.get(self.uow.session, org_id)
        if not org:
            raise NotFoundDomainError(f"Organization '{org_id}' not found.")

        update_data = obj_in.model_dump(exclude_unset=True)
        # Financial rule: slug is immutable once set. Strip it defensively so
        # that future schema drift cannot accidentally write through to the DB.
        update_data.pop("slug", None)

        updated_org = await self.uow.organizations.update(
            self.uow.session,
            db_obj=org,
            obj_in=update_data
        )

        await self.record_audit(
            action="update",
            resource_type="organization",
            resource_id=str(org_id),
            payload=update_data
        )

        await self.uow.commit()
        return updated_org
