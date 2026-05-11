from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.grn import GRN, GRNLineItem

class GRNRepository(BaseRepository[GRN]):
    """
    Repository for Goods Receipt Note operations.
    Inherits tenant-safe isolation from BaseRepository.
    """
    def __init__(self):
        super().__init__(GRN)

    async def get_by_grn_number(
        self,
        session,
        organization_id: uuid.UUID,
        grn_number: str
    ) -> Optional[GRN]:
        """Retrieve a GRN by its number within a specific organization."""
        query = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.grn_number == grn_number,
            self.model.is_deleted == False
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_items(
        self,
        session,
        organization_id: uuid.UUID,
        id: uuid.UUID
    ) -> Optional[GRN]:
        """Retrieve a tenant-scoped GRN with its line items eagerly loaded."""
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
        
    async def list_by_po_id(
        self,
        session,
        organization_id: uuid.UUID,
        po_id: uuid.UUID
    ) -> List[GRN]:
        """List all GRNs for a specific Purchase Order."""
        query = (
            select(self.model)
            .where(
                self.model.po_id == po_id,
                self.model.organization_id == organization_id,
                self.model.is_deleted == False
            )
            .options(selectinload(self.model.line_items))
        )
        result = await session.execute(query)
        return list(result.scalars().all())

class GRNLineItemRepository(BaseRepository[GRNLineItem]):
    """
    Repository for GRN Line Item operations.
    """
    def __init__(self):
        super().__init__(GRNLineItem)
