from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.purchase_order import PurchaseOrder, POLineItem

class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """
    Repository for Purchase Order operations.
    Inherits tenant-safe isolation from BaseRepository.
    """
    def __init__(self):
        super().__init__(PurchaseOrder)

    async def get_by_po_number(
        self,
        session,
        organization_id: uuid.UUID,
        po_number: str
    ) -> Optional[PurchaseOrder]:
        """Retrieve a PO by its number within a specific organization."""
        query = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.po_number == po_number,
            self.model.is_deleted == False
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_items(
        self,
        session,
        organization_id: uuid.UUID,
        id: uuid.UUID
    ) -> Optional[PurchaseOrder]:
        """Retrieve a tenant-scoped PO with its line items eagerly loaded."""
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

class POLineItemRepository(BaseRepository[POLineItem]):
    """
    Repository for PO Line Item operations.
    """
    def __init__(self):
        super().__init__(POLineItem)
