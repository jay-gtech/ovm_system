from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.document import (
    DocumentType,
    DocumentProcessingStatus,
    DocumentValidationStatus,
    DocumentHumanReviewStatus,
    ExtractionStatus
)

class DocumentBase(BaseModel):
    document_type: DocumentType
    original_filename: str
    mime_type: str
    file_size: int
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[UUID] = None

class DocumentCreate(DocumentBase):
    storage_path: str
    uploaded_by_user_id: UUID

class DocumentUpdate(BaseModel):
    processing_status: Optional[DocumentProcessingStatus] = None
    validation_status: Optional[DocumentValidationStatus] = None
    human_review_status: Optional[DocumentHumanReviewStatus] = None
    review_required: Optional[bool] = None

class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    storage_path: str
    file_size: int
    uploaded_by_user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentExtractionResponse(BaseModel):
    id: UUID
    document_id: UUID
    extraction_engine: str
    extraction_status: ExtractionStatus
    raw_ocr_text: Optional[str] = None
    extracted_fields_json: Optional[Dict[str, Any]] = None
    confidence_scores_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: UUID
    organization_id: UUID
    storage_path: str
    uploaded_by_user_id: UUID
    uploaded_at: datetime
    processing_status: DocumentProcessingStatus
    review_required: bool
    validation_status: DocumentValidationStatus
    human_review_status: DocumentHumanReviewStatus
    created_at: datetime
    updated_at: datetime
    
    versions: Optional[List[DocumentVersionResponse]] = []
    extractions: Optional[List[DocumentExtractionResponse]] = []

    class Config:
        from_attributes = True
