import uuid
from typing import Sequence, Tuple
from sqlalchemy.exc import IntegrityError
from app.services.base import BaseService
from app.services.audit import AuditService
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorStatusUpdate
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
)

# Fields whose changes carry financial/operational significance and must be audited.
# Excludes cosmetic fields (display_name, notes) per spec requirements.
_SENSITIVE_VENDOR_FIELDS = frozenset({"legal_name", "tax_id", "email", "phone", "address"})


class VendorService(BaseService):
    """
    Service for managing Vendor lifecycle.
    Enforces financial-system rules and tenant isolation.
    """

    async def create_vendor(self, obj_in: VendorCreate) -> Vendor:
        """
        Create a new vendor.
        Rule: vendor_code must be unique per tenant.
        """
        async with self.uow:
            # Optimistic pre-check (catches most duplicates without hitting the DB constraint)
            existing = await self.uow.vendors.get_by_code(
                self.uow.session,
                vendor_code=obj_in.vendor_code
            )
            if existing:
                raise ConflictDomainError(
                    f"Vendor with code '{obj_in.vendor_code}' already exists."
                )

            vendor_data = obj_in.model_dump()
            try:
                vendor = await self.uow.vendors.create(
                    self.uow.session,
                    obj_in=vendor_data
                )

                await AuditService.log_event(
                    self.uow.session,
                    entity_type="vendor",
                    entity_id=vendor.id,
                    action="VENDOR_CREATED",
                    metadata={
                        "vendor_code": vendor.vendor_code,
                        "legal_name": vendor.legal_name,
                        "status": vendor.status.value,
                    },
                )

                await self.uow.commit()
            except IntegrityError:
                # FIX-1: Race condition — two concurrent creates both passed the pre-check.
                # The DB unique constraint fired. Surface as a domain conflict.
                raise ConflictDomainError(
                    f"Vendor with code '{obj_in.vendor_code}' already exists."
                )
            return vendor

    async def get_vendor(self, vendor_id: uuid.UUID) -> Vendor:
        """Fetch a vendor by ID. Enforces tenant isolation."""
        async with self.uow:
            vendor = await self.uow.vendors.get(self.uow.session, id=vendor_id)
            if not vendor:
                raise NotFoundDomainError(f"Vendor with ID {vendor_id} not found.")
            return vendor

    async def list_vendors(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[Sequence[Vendor], int]:
        """
        List vendors with pagination. Enforces tenant isolation.
        Returns (items, total_count) for accurate pagination metadata.
        """
        async with self.uow:
            items = await self.uow.vendors.get_multi(
                self.uow.session,
                skip=skip,
                limit=limit
            )
            total = await self.uow.vendors.count(self.uow.session)
            return items, total

    async def update_vendor(
        self,
        vendor_id: uuid.UUID,
        obj_in: VendorUpdate
    ) -> Vendor:
        """
        Update vendor details.
        Rule: vendor_code is immutable.
        Audits only sensitive operational fields; cosmetic fields (display_name, notes) are silent.
        """
        async with self.uow:
            vendor = await self.uow.vendors.get(self.uow.session, id=vendor_id)
            if not vendor:
                raise NotFoundDomainError(f"Vendor with ID {vendor_id} not found.")

            update_data = obj_in.model_dump(exclude_unset=True)
            # FIX-2: Immutability enforcement — financial identifiers must never be mutated.
            update_data.pop("vendor_code", None)
            # FIX-2: Status changes MUST go through update_status().
            update_data.pop("status", None)

            # Emit one audit entry per sensitive field that actually changes value
            for field in _SENSITIVE_VENDOR_FIELDS:
                if field in update_data:
                    old_val = getattr(vendor, field, None)
                    new_val = update_data[field]
                    if old_val != new_val:
                        await AuditService.log_event(
                            self.uow.session,
                            entity_type="vendor",
                            entity_id=vendor.id,
                            action="VENDOR_UPDATED",
                            field_name=field,
                            old_value=str(old_val) if old_val is not None else None,
                            new_value=str(new_val) if new_val is not None else None,
                        )

            updated_vendor = await self.uow.vendors.update(
                self.uow.session,
                db_obj=vendor,
                obj_in=update_data
            )

            await self.uow.commit()
            return updated_vendor

    async def update_status(
        self,
        vendor_id: uuid.UUID,
        obj_in: VendorStatusUpdate
    ) -> Vendor:
        """Update vendor status (lifecycle management)."""
        async with self.uow:
            vendor = await self.uow.vendors.get(self.uow.session, id=vendor_id)
            if not vendor:
                raise NotFoundDomainError(f"Vendor with ID {vendor_id} not found.")

            previous_status = vendor.status.value if vendor.status else None

            updated_vendor = await self.uow.vendors.update(
                self.uow.session,
                db_obj=vendor,
                obj_in={"status": obj_in.status}
            )

            await AuditService.log_event(
                self.uow.session,
                entity_type="vendor",
                entity_id=vendor.id,
                action="VENDOR_STATUS_CHANGED",
                field_name="status",
                old_value=previous_status,
                new_value=obj_in.status.value,
            )

            await self.uow.commit()
            return updated_vendor
