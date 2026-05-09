import asyncio
import logging
from uuid import UUID
from pathlib import Path

from app.models.document import DocumentProcessingStatus, ExtractionStatus
from app.core.context import set_tenant_id
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.audit import AuditService

# Try to import OCR tools, if missing we will mock or raise
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract or pdf2image not found. OCR processing will be simulated.")

logger = logging.getLogger(__name__)

async def run_ocr_pipeline(file_path: str, mime_type: str) -> str:
    """Run Tesseract OCR on a file."""
    if not OCR_AVAILABLE:
        # Mock OCR output for testing without Tesseract installed
        await asyncio.sleep(1) # Simulate processing
        return "MOCK OCR TEXT: Invoice Number 12345, Amount: $1000.00, Vendor: Acme Corp"

    def _sync_ocr():
        text = ""
        try:
            if mime_type == "application/pdf":
                images = convert_from_path(file_path)
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
        except Exception as e:
            logger.error(f"OCR Error on {file_path}: {e}")
            raise e
        return text
    
    loop = asyncio.get_running_loop()
    raw_text = await loop.run_in_executor(None, _sync_ocr)
    return raw_text

async def process_document_ocr(tenant_id: UUID, document_id: UUID):
    """
    Background task to run OCR on an uploaded document.
    """
    async with SQLAlchemyUnitOfWork() as uow:
        # Re-establish context in background task
        set_tenant_id(tenant_id)
        
        document = await uow.documents.get(uow.session, document_id)
        if not document:
            logger.error(f"Document {document_id} not found for OCR.")
            return
            
        try:
            raw_text = await run_ocr_pipeline(document.storage_path, document.mime_type)
            
            # Store OCR result in DocumentExtraction
            extraction_in = {
                "document_id": document.id,
                "extraction_engine": "tesseract",
                "extraction_status": ExtractionStatus.PENDING,  # PENDING because parsing comes next
                "raw_ocr_text": raw_text
            }
            await uow.documents.add_extraction(uow.session, extraction_in)
            
            # Update Document status — use repo.update() only; avoid redundant direct attribute set
            old_status = document.processing_status
            await uow.documents.update(uow.session, db_obj=document, obj_in={"processing_status": DocumentProcessingStatus.OCR_COMPLETE})
            
            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="OCR_COMPLETE",
                field_name="processing_status",
                old_value=old_status,
                new_value=DocumentProcessingStatus.OCR_COMPLETE
            )
            await uow.commit()
            
            logger.info(f"OCR complete for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed OCR for document {document_id}: {e}")
            old_status = document.processing_status
            await uow.documents.update(uow.session, db_obj=document, obj_in={"processing_status": DocumentProcessingStatus.FAILED})
            
            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="OCR_FAILED",
                field_name="processing_status",
                old_value=old_status,
                new_value=DocumentProcessingStatus.FAILED,
                reason=str(e)
            )
            await uow.commit()

