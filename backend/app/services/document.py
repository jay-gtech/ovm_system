import os
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentType, DocumentProcessingStatus
from app.core.context import require_tenant_id
from app.core.config import settings
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.audit import AuditService

UPLOAD_DIR = os.getenv("OVM_UPLOAD_DIR", "uploads")

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/png": "png"
}

class DocumentService:
    @staticmethod
    async def upload_document(
        db: AsyncSession,
        file: UploadFile,
        document_type: DocumentType,
        user_id: uuid.UUID
    ) -> Document:
        tenant_id = require_tenant_id()

        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes."
            )
            
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file."
            )

        # Create tenant-isolated secure directory
        tenant_dir = Path(UPLOAD_DIR) / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe unique filename
        ext = ALLOWED_MIME_TYPES[file.content_type]
        safe_filename = f"{uuid.uuid4().hex}_{int(datetime.now(timezone.utc).timestamp())}.{ext}"
        storage_path = tenant_dir / safe_filename
        
        # Save file securely
        async with aiofiles.open(storage_path, 'wb') as out_file:
            await out_file.write(content)
            
        async with SQLAlchemyUnitOfWork(session=db) as uow:
            # Create database record
            doc_in = {
                "document_type": document_type,
                "original_filename": file.filename,
                "storage_path": str(storage_path),
                "mime_type": file.content_type,
                "file_size": file_size,
                "uploaded_by_user_id": user_id,
                "processing_status": DocumentProcessingStatus.UPLOADED,
            }
            
            document = await uow.documents.create(uow.session, obj_in=doc_in)
            
            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="DOCUMENT_UPLOADED",
                actor_user_id=user_id,
                metadata={
                    "filename": file.filename,
                    "mime_type": file.content_type,
                    "size": file_size,
                    "document_type": document_type
                }
            )
            await uow.commit()
            
        return document

document_service = DocumentService()
