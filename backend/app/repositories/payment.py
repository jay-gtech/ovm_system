from typing import Sequence
import uuid
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.payment import Payment, PaymentStatus
from app.db.tenancy import apply_tenant_scope

class PaymentRepository(BaseRepository[Payment]):
    def __init__(self):
        super().__init__(Payment)

    async def get_by_invoice(
        self, db: AsyncSession, invoice_id: uuid.UUID
    ) -> Sequence[Payment]:
        """
        Fetch all non-deleted payments for a specific invoice (tenant-scoped).
        """
        query = select(self.model).where(self.model.invoice_id == invoice_id)

        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        query = apply_tenant_scope(query, self.model)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_received_sum_by_invoice(
        self, db: AsyncSession, invoice_id: uuid.UUID
    ) -> Decimal:
        """
        FI-1: Returns the exact Decimal sum of all RECEIVED payments for an invoice.
        Avoids float conversion which loses precision on Numeric(18,4) columns.
        Defaults to Decimal("0") — not 0.0 — to keep all arithmetic in Decimal space.
        """
        query = select(func.sum(self.model.amount)).where(
            self.model.invoice_id == invoice_id,
            self.model.status == PaymentStatus.RECEIVED
        )

        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        query = apply_tenant_scope(query, self.model)

        result = await db.execute(query)
        value = result.scalar()
        return value if value is not None else Decimal("0")
