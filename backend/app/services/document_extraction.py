import re
import logging
from uuid import UUID
from typing import Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import DocumentType, DocumentProcessingStatus, ExtractionStatus, DocumentExtraction
from app.repositories.document import document_repo
from app.db.session import SessionLocal
from app.core.context import set_tenant_id

logger = logging.getLogger(__name__)

class ExtractionEngine:
    @staticmethod
    def extract_invoice(text: str) -> Dict[str, Any]:
        """Deterministic regex-based extraction for invoices."""
        data = {}
        confidence = {}

        # Invoice Number
        inv_match = re.search(r'(?i)invoice\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9\-]+)', text)
        if inv_match:
            data['invoice_number'] = inv_match.group(1)
            confidence['invoice_number'] = str(Decimal('0.9'))  # Decimal serialization to string
            
        # Invoice Date
        date_match = re.search(r'(?i)(?:invoice\s*)?date\s*[:\-]?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{1,4})', text)
        if date_match:
            data['invoice_date'] = date_match.group(1)
            confidence['invoice_date'] = str(Decimal('0.8'))  # Decimal serialization to string
            
        # Due Date
        due_match = re.search(r'(?i)due\s*date\s*[:\-]?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{1,4})', text)
        if due_match:
            data['due_date'] = due_match.group(1)
            confidence['due_date'] = str(Decimal('0.8'))  # Decimal serialization to string

        # PO Reference
        po_match = re.search(r'(?i)(?:po|purchase\s*order)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9\-]+)', text)
        if po_match:
            data['po_reference'] = po_match.group(1)
            confidence['po_reference'] = str(Decimal('0.85'))  # Decimal serialization to string

        # Amounts — store as Decimal strings in JSONB to prevent float precision loss
        amounts = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2}))', text)
        if amounts:
            amounts_d = sorted([Decimal(a.replace(',', '')) for a in amounts])
            data['total_amount'] = str(amounts_d[-1])      # string to preserve precision
            confidence['total_amount'] = str(Decimal('0.7'))  # Decimal serialization to string
            if len(amounts_d) > 1:
                data['subtotal_amount'] = str(amounts_d[-2])
                confidence['subtotal_amount'] = str(Decimal('0.6'))  # Decimal serialization to string

        return data, confidence

    @staticmethod
    def extract_purchase_order(text: str) -> Dict[str, Any]:
        """Deterministic regex-based extraction for purchase orders."""
        data = {}
        confidence = {}

        # PO Number
        po_match = re.search(r'(?i)(?:po|purchase\s*order)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9\-]+)', text)
        if po_match:
            data['po_number'] = po_match.group(1)
            confidence['po_number'] = str(Decimal('0.9'))  # Decimal serialization to string

        # Issue Date
        date_match = re.search(r'(?i)(?:issue\s*)?date\s*[:\-]?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{1,4})', text)
        if date_match:
            data['issue_date'] = date_match.group(1)
            confidence['issue_date'] = str(Decimal('0.8'))  # Decimal serialization to string

        # Amounts — store as Decimal strings in JSONB to prevent float precision loss
        amounts = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2}))', text)
        if amounts:
            amounts_d = sorted([Decimal(a.replace(',', '')) for a in amounts])
            data['expected_amount'] = str(amounts_d[-1])   # string to preserve precision
            confidence['expected_amount'] = str(Decimal('0.7'))  # Decimal serialization to string

        return data, confidence

from app.services.uow import SQLAlchemyUnitOfWork
from app.services.audit import AuditService

async def process_document_extraction(tenant_id: UUID, document_id: UUID):
    """
    Background task to run Extraction on OCR'ed document.
    """
    async with SQLAlchemyUnitOfWork() as uow:
        set_tenant_id(tenant_id)
        
        document = await uow.documents.get_with_relations(uow.session, document_id)
        if not document or document.processing_status != DocumentProcessingStatus.OCR_COMPLETE:
            logger.error(f"Document {document_id} not ready for extraction.")
            return
            
        try:
            # Get latest extraction record with OCR text
            extraction = await uow.document_extractions.get_latest_for_document(uow.session, document_id)
            
            if not extraction or not extraction.raw_ocr_text:
                raise ValueError("No OCR text available for extraction")
                
            text = extraction.raw_ocr_text
            extracted_data = {}
            confidence = {}
            
            if document.document_type == DocumentType.INVOICE:
                extracted_data, confidence = ExtractionEngine.extract_invoice(text)
            elif document.document_type == DocumentType.PURCHASE_ORDER:
                extracted_data, confidence = ExtractionEngine.extract_purchase_order(text)
            
            # --- Transactional Boundary: Atomic update of extraction results and document status ---
            await uow.document_extractions.update(
                uow.session, 
                db_obj=extraction, 
                obj_in={
                    "extracted_fields_json": extracted_data,
                    "confidence_scores_json": confidence,
                    "extraction_status": ExtractionStatus.SUCCESS
                }
            )
            
            old_status = document.processing_status
            await uow.documents.update(uow.session, db_obj=document, obj_in={"processing_status": DocumentProcessingStatus.EXTRACTION_COMPLETE})
            
            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="EXTRACTION_COMPLETE",
                field_name="processing_status",
                old_value=old_status,
                new_value=DocumentProcessingStatus.EXTRACTION_COMPLETE,
                metadata={"extracted_fields": extracted_data}
            )
            # Explicit commit: ensures extraction data and status change are atomic
            await uow.commit()
            
            logger.info(f"Extraction complete for document {document_id}")
            
        except Exception as e:
            # --- Transactional Boundary: Rollback occurs automatically via __aexit__ on exception ---
            logger.error(f"Failed Extraction for document {document_id}: {e}")
            old_status = document.processing_status
            
            # Start a new transaction for error state logging
            async with SQLAlchemyUnitOfWork() as error_uow:
                doc = await error_uow.documents.get(error_uow.session, document_id)
                if doc:
                    await error_uow.documents.update(error_uow.session, db_obj=doc, obj_in={"processing_status": DocumentProcessingStatus.FAILED})
                    
                    await AuditService.log_event(
                        session=error_uow.session,
                        entity_type="DOCUMENT",
                        entity_id=doc.id,
                        action="EXTRACTION_FAILED",
                        field_name="processing_status",
                        old_value=old_status,
                        new_value=DocumentProcessingStatus.FAILED,
                        reason=str(e)
                    )
                    await error_uow.commit()

