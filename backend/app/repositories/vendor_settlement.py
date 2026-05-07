import uuid
from decimal import Decimal
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.db.tenancy import apply_tenant_scope

class VendorSettlementRepository(BaseRepository[VendorSettlement]):
    def __init__(self):
        super().__init__(VendorSettlement)

    async def get_by_reference(
        self, db: AsyncSession, organization_id: uuid.UUID, settlement_reference: str
    ) -> VendorSettlement | None:
        query = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.settlement_reference == settlement_reference
        )
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_settled_sum_by_payment(
        self, db: AsyncSession, payment_id: uuid.UUID
    ) -> Decimal:
        query = select(func.sum(self.model.amount)).where(
            self.model.payment_id == payment_id,
            self.model.status.in_([SettlementStatus.PENDING, SettlementStatus.SETTLED])
        )
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))
        query = apply_tenant_scope(query, self.model)
        result = await db.execute(query)
        value = result.scalar()
        return value if value is not None else Decimal("0")
