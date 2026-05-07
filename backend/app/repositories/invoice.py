from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.invoice import Invoice, InvoiceLineItem

class InvoiceRepository(BaseRepository[Invoice]):
    """
    Repository for Invoice operations.
    Inherits tenant-safe isolation from BaseRepository.
    """
    def __init__(self):
        super().__init__(Invoice)

    async def get_by_invoice_number(
        self,
        session,
        organization_id: uuid.UUID,
        invoice_number: str
    ) -> Optional[Invoice]:
        """Retrieve an Invoice by its number within a specific organization."""
        query = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.invoice_number == invoice_number,
            self.model.is_deleted == False
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_items(
        self,
        session,
        organization_id: uuid.UUID,
        id: uuid.UUID
    ) -> Optional[Invoice]:
        """Retrieve a tenant-scoped Invoice with its line items eagerly loaded."""
        query = (
            select(self.model)
            .where(
                self.model.id == id,
                self.model.organization_id == organization_id,
                self.model.is_deleted == False
            )
            .options(selectinload(self.model.line_items))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

class InvoiceLineItemRepository(BaseRepository[InvoiceLineItem]):
    """
    Repository for Invoice Line Item operations.
    """
    def __init__(self):
        super().__init__(InvoiceLineItem)
