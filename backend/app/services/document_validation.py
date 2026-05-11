import logging
from uuid import UUID
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.document import Document, DocumentType, DocumentValidationStatus, DocumentProcessingStatus
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.models.vendor import Vendor
from app.models.alert import AlertType, AlertSeverity
from app.repositories.document import document_repo
from app.db.session import SessionLocal
from app.core.context import set_tenant_id
from app.db.tenancy import apply_tenant_scope

logger = logging.getLogger(__name__)

TOLERANCE_AMOUNT = Decimal("0.50")  # Acceptable variance

class ValidationEngine:
    @staticmethod
    async def validate_invoice(db: AsyncSession, document: Document, extracted: Dict[str, Any]) -> List[str]:
        """Validates extracted invoice data and returns a list of mismatch/error strings."""
        mismatches = []

        invoice_num = extracted.get("invoice_number")
        po_num = extracted.get("po_reference")
        # Amounts in JSONB are stored as strings to preserve Decimal precision
        total_amt_raw = extracted.get("total_amount")
        total_amt = Decimal(str(total_amt_raw)) if total_amt_raw is not None else None

        # --- Tenant-scoped duplicate invoice check ---
        # Enforcement: apply_tenant_scope ensures we only check invoices for the active organization.
        existing_invoice = None
        if invoice_num:
            query = apply_tenant_scope(
                select(Invoice).where(Invoice.invoice_number == invoice_num),
                Invoice
            )
            result = await db.execute(query)
            existing_invoice = result.scalars().first()
            if existing_invoice:
                mismatches.append(f"Duplicate invoice number detected: {invoice_num}")

        # --- Tenant-scoped PO lookup ---
        # Enforcement: apply_tenant_scope prevents cross-tenant PO access even if po_number is known.
        po_record = None
        if po_num:
            query = apply_tenant_scope(
                select(PurchaseOrder).where(PurchaseOrder.po_number == po_num),
                PurchaseOrder
            )
            result = await db.execute(query)
            po_record = result.scalars().first()
            if not po_record:
                mismatches.append(f"Purchase Order not found: {po_num}")

        # --- Tenant-scoped Vendor validation ---
        # Enforcement: apply_tenant_scope ensures we only validate against vendors owned by the tenant.
        vendor_name = extracted.get("vendor_name")
        if vendor_name:
            query = apply_tenant_scope(
                select(Vendor).where(Vendor.legal_name == vendor_name),
                Vendor
            )
            result = await db.execute(query)
            vendor_record = result.scalars().first()
            if not vendor_record:
                mismatches.append(f"Vendor not recognized in master data: {vendor_name}")
            elif po_record and po_record.vendor_id != vendor_record.id:
                mismatches.append(f"Vendor mismatch: PO belongs to {po_record.vendor.display_name}, but Invoice is from {vendor_name}")

        # --- Explicit link priority: PO > Invoice (PO is the authoritative workflow entity) ---
        if po_record:
            document.linked_entity_type = "PURCHASE_ORDER"
            document.linked_entity_id = po_record.id
        elif existing_invoice:
            document.linked_entity_type = "INVOICE"
            document.linked_entity_id = existing_invoice.id

        # --- Amount variance check against PO ---
        if po_record and total_amt is not None:
            if hasattr(po_record, 'total_amount') and po_record.total_amount is not None:
                diff = abs(po_record.total_amount - total_amt)
                if diff > TOLERANCE_AMOUNT:
                    mismatches.append(
                        f"Amount variance detected: PO is {po_record.total_amount}, Document is {total_amt}"
                    )

        if not po_num and not invoice_num:
            mismatches.append("Missing critical workflow linkages (PO or Invoice Number)")

        return mismatches

    @staticmethod
    async def validate_purchase_order(db: AsyncSession, document: Document, extracted: Dict[str, Any]) -> List[str]:
        mismatches = []
        po_num = extracted.get("po_number")

        if po_num:
            # --- Tenant-scoped PO lookup ---
            # Enforcement: apply_tenant_scope ensures PO belongs to the active organization.
            query = apply_tenant_scope(
                select(PurchaseOrder).where(PurchaseOrder.po_number == po_num),
                PurchaseOrder
            )
            result = await db.execute(query)
            existing_po = result.scalars().first()
            if existing_po:
                document.linked_entity_type = "PURCHASE_ORDER"
                document.linked_entity_id = existing_po.id

                # Amounts in JSONB stored as strings — parse through Decimal
                ext_amt_raw = extracted.get("expected_amount")
                if ext_amt_raw is not None and hasattr(existing_po, 'total_amount') and existing_po.total_amount is not None:
                    ext_dec = Decimal(str(ext_amt_raw))
                    if abs(existing_po.total_amount - ext_dec) > TOLERANCE_AMOUNT:
                        mismatches.append(f"Amount variance: DB has {existing_po.total_amount}, Doc has {ext_dec}")

        return mismatches

from app.services.uow import SQLAlchemyUnitOfWork
from app.services.audit import AuditService

async def create_validation_alert(uow: SQLAlchemyUnitOfWork, document: Document, message: str):
    """Integrates with Mismatch Alert engine with strict tenant isolation."""
    alert_in = {
        "organization_id": document.organization_id,  # Enforcement: Explicit tenant assignment
        "alert_type": AlertType.WORKFLOW_STALL,       # Corrected enum
        "severity": AlertSeverity.HIGH,
        "entity_type": "DOCUMENT",
        "entity_id": document.id,
        "title": "Document Validation Mismatch",
        "message": f"Document Validation Mismatch [Doc {document.id}]: {message}",
        "metadata_json": {
            "document_id": str(document.id),
            "document_type": document.document_type
        }
    }
    # Note: AlertRepository.create does not inherit from BaseRepository, 
    # so we must pass organization_id explicitly in alert_in.
    await uow.alerts.create(uow.session, obj_in=alert_in)

async def process_document_validation(tenant_id: UUID, document_id: UUID):
    async with SQLAlchemyUnitOfWork() as uow:
        # Enforcement: Set tenant context for all subsequent repo/query calls.
        set_tenant_id(tenant_id)
        
        # Enforcement: get_with_relations uses apply_tenant_scope to prevent cross-tenant access.
        document = await uow.documents.get_with_relations(uow.session, document_id)
        if not document or document.processing_status != DocumentProcessingStatus.EXTRACTION_COMPLETE:
            return
            
        extraction = document.extractions[-1] if document.extractions else None
        if not extraction or not extraction.extracted_fields_json:
            old_val_status = document.validation_status
            
            # --- Transactional Boundary: Set FAILED status if no extraction found ---
            await uow.document_validations.update_validation_status(
                uow.session, 
                document=document, 
                status=DocumentValidationStatus.FAILED
            )
            
            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="VALIDATION_FAILED",
                field_name="validation_status",
                old_value=old_val_status,
                new_value=DocumentValidationStatus.FAILED,
                reason="No extracted fields available"
            )
            # Explicit commit
            await uow.commit()
            return

        mismatches = []
        try:
            if document.document_type == DocumentType.INVOICE:
                mismatches = await ValidationEngine.validate_invoice(uow.session, document, extraction.extracted_fields_json)
            elif document.document_type == DocumentType.PURCHASE_ORDER:
                mismatches = await ValidationEngine.validate_purchase_order(uow.session, document, extraction.extracted_fields_json)
            
            old_val_status = document.validation_status
            
            # --- Transactional Boundary: Atomic update of validation results and status ---
            if mismatches:
                # Create alerts for mismatches
                for m in mismatches:
                    await create_validation_alert(uow, document, m)
                
                await uow.document_validations.update_validation_status(
                    uow.session,
                    document=document,
                    status=DocumentValidationStatus.FAILED,
                    processing_status=DocumentProcessingStatus.VALIDATED
                )
            else:
                await uow.document_validations.update_validation_status(
                    uow.session,
                    document=document,
                    status=DocumentValidationStatus.PASSED,
                    processing_status=DocumentProcessingStatus.VALIDATED
                )

            await AuditService.log_event(
                session=uow.session,
                entity_type="DOCUMENT",
                entity_id=document.id,
                action="VALIDATION_COMPLETE",
                field_name="validation_status",
                old_value=old_val_status,
                new_value=document.validation_status,
                metadata={"mismatches": mismatches}
            )
            # Explicit commit: ensures all alerts and status changes are atomic
            await uow.commit()
            
            logger.info(f"Validation complete for document {document_id}")
            
        except Exception as e:
            # --- Transactional Boundary: Rollback occurs automatically via __aexit__ on exception ---
            logger.error(f"Failed Validation for document {document_id}: {e}")
            old_proc_status = document.processing_status
            
            # Start a new transaction for error state logging
            async with SQLAlchemyUnitOfWork() as error_uow:
                doc = await error_uow.documents.get(error_uow.session, document_id)
                if doc:
                    await error_uow.documents.update(error_uow.session, db_obj=doc, obj_in={"processing_status": DocumentProcessingStatus.FAILED})
                    
                    await AuditService.log_event(
                        session=error_uow.session,
                        entity_type="DOCUMENT",
                        entity_id=doc.id,
                        action="VALIDATION_ERROR",
                        field_name="processing_status",
                        old_value=old_proc_status,
                        new_value=DocumentProcessingStatus.FAILED,
                        reason=str(e)
                    )
                    await error_uow.commit()

