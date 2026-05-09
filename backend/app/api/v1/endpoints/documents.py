import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.document import DocumentType, DocumentHumanReviewStatus
from app.schemas.document import DocumentResponse, DocumentExtractionResponse
from app.services.document import document_service
from app.repositories.document import document_repo
from app.core.context import require_tenant_id

# Import processing tasks
from app.services.ocr import process_document_ocr
from app.services.document_extraction import process_document_extraction
from app.services.document_validation import process_document_validation

router = APIRouter()

async def idp_pipeline(tenant_id: uuid.UUID, document_id: uuid.UUID):
    """
    Orchestrates the IDP background pipeline sequentially.
    
    Stage flow:
    1. UPLOAD (Sync via API)
    2. OCR -> Extracts raw text from document image/PDF
    3. EXTRACTION -> Applies regex/ML rules to extract financial fields
    4. VALIDATION -> Checks for mismatches against vendor master/PO records
    5. HUMAN REVIEW -> Flagged for approval/rejection (Sync via API)
    """
    await process_document_ocr(tenant_id, document_id)
    await process_document_extraction(tenant_id, document_id)
    await process_document_validation(tenant_id, document_id)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload a document for processing.
    """
    document = await document_service.upload_document(
        db=db,
        file=file,
        document_type=document_type,
        user_id=current_user.id
    )
    
    tenant_id = require_tenant_id()
    background_tasks.add_task(idp_pipeline, tenant_id, document.id)
    
    return document

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    processing_status: Optional[str] = Query(None),
    human_review_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve documents.
    """
    documents = await document_repo.get_multi_filtered(
        db, 
        skip=skip, 
        limit=limit,
        processing_status=processing_status,
        human_review_status=human_review_status
    )
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get document by ID.
    """
    document = await document_repo.get_with_relations(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/extraction", response_model=List[DocumentExtractionResponse])
async def get_document_extractions(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get document extraction history.
    """
    document = await document_repo.get_with_relations(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document.extractions

@router.get("/{document_id}/validation")
async def get_document_validation(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get document validation status and linked entities.
    """
    document = await document_repo.get_with_relations(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "validation_status": document.validation_status,
        "linked_entity_type": document.linked_entity_type,
        "linked_entity_id": document.linked_entity_id,
        "processing_status": document.processing_status
    }

from app.services.audit import AuditService

@router.post("/{document_id}/review/approve", response_model=DocumentResponse)
async def approve_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Human review: Approve document extraction/validation.
    Requires document to be fully VALIDATED and pending review.
    """
    from app.models.document import DocumentProcessingStatus, DocumentValidationStatus
    document = await document_repo.get_with_relations(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # --- Backend-authoritative state guards ---
    if document.processing_status != DocumentProcessingStatus.VALIDATED:
        raise HTTPException(
            status_code=422,
            detail=f"Document must reach VALIDATED status before review. Current: {document.processing_status}"
        )
    if not document.review_required:
        raise HTTPException(status_code=422, detail="Document does not require human review.")
    if document.human_review_status != DocumentHumanReviewStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Review already completed with status: {document.human_review_status}"
        )

    old_status = document.human_review_status
    await document_repo.update(db, db_obj=document, obj_in={"human_review_status": DocumentHumanReviewStatus.APPROVED})

    await AuditService.log_event(
        session=db,
        entity_type="DOCUMENT",
        entity_id=document.id,
        action="REVIEW_APPROVED",
        actor_user_id=current_user.id,
        field_name="human_review_status",
        old_value=old_status,
        new_value=DocumentHumanReviewStatus.APPROVED
    )
    return document

@router.post("/{document_id}/review/reject", response_model=DocumentResponse)
async def reject_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Human review: Reject document extraction/validation.
    Requires document review to be in PENDING state.
    """
    document = await document_repo.get_with_relations(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # --- Backend-authoritative state guards ---
    if not document.review_required:
        raise HTTPException(status_code=422, detail="Document does not require human review.")
    if document.human_review_status != DocumentHumanReviewStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Review already completed with status: {document.human_review_status}"
        )

    old_status = document.human_review_status
    await document_repo.update(db, db_obj=document, obj_in={"human_review_status": DocumentHumanReviewStatus.REJECTED})

    await AuditService.log_event(
        session=db,
        entity_type="DOCUMENT",
        entity_id=document.id,
        action="REVIEW_REJECTED",
        actor_user_id=current_user.id,
        field_name="human_review_status",
        old_value=old_status,
        new_value=DocumentHumanReviewStatus.REJECTED
    )
    return document
