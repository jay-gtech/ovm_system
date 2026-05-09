import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentVersion, DocumentExtraction
from app.repositories.base import BaseRepository
from app.db.tenancy import apply_tenant_scope

class DocumentRepository(BaseRepository[Document]):
    def __init__(self):
        super().__init__(Document)

    async def get_with_relations(self, db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.versions),
                selectinload(self.model.extractions)
            )
            .where(self.model.id == document_id)
            .where(self.model.is_deleted.is_(False))
        )
        query = apply_tenant_scope(query, self.model)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_filtered(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        processing_status: Optional[str] = None,
        human_review_status: Optional[str] = None
    ) -> Sequence[Document]:
        query = select(self.model).where(self.model.is_deleted.is_(False))
        
        if processing_status:
            query = query.where(self.model.processing_status == processing_status)
        if human_review_status:
            query = query.where(self.model.human_review_status == human_review_status)
            
        query = apply_tenant_scope(query, self.model)
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def add_version(self, db: AsyncSession, version_in: dict) -> DocumentVersion:
        from app.core.context import require_tenant_id
        if "organization_id" not in version_in:
            version_in["organization_id"] = require_tenant_id()
        version = DocumentVersion(**version_in)
        db.add(version)
        await db.flush()
        return version

    async def add_extraction(self, db: AsyncSession, extraction_in: dict) -> DocumentExtraction:
        from app.core.context import require_tenant_id
        if "organization_id" not in extraction_in:
            extraction_in["organization_id"] = require_tenant_id()
        extraction = DocumentExtraction(**extraction_in)
        db.add(extraction)
        await db.flush()
        return extraction

document_repo = DocumentRepository()
