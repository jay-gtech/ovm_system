from enum import Enum
from datetime import datetime, timezone
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, Enum as SQLEnum, ForeignKey, UUID, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import FullBaseModel

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User

class DocumentType(str, Enum):
    INVOICE = "INVOICE"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    OTHER = "OTHER"

class DocumentProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    OCR_COMPLETE = "OCR_COMPLETE"
    EXTRACTION_COMPLETE = "EXTRACTION_COMPLETE"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"

class DocumentValidationStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"

class DocumentHumanReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Document(FullBaseModel):
    """
    Intelligent Document Processing (IDP) base document record.
    """
    document_type: Mapped[DocumentType] = mapped_column(String(50), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        String(50), 
        default=DocumentProcessingStatus.UPLOADED, 
        nullable=False
    )

    linked_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linked_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # IDP workflow specific states
    review_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    validation_status: Mapped[DocumentValidationStatus] = mapped_column(
        String(50),
        default=DocumentValidationStatus.PENDING,
        nullable=False
    )
    human_review_status: Mapped[DocumentHumanReviewStatus] = mapped_column(
        String(50),
        default=DocumentHumanReviewStatus.PENDING,
        nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization")
    uploaded_by: Mapped["User"] = relationship("User")
    
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    extractions: Mapped[List["DocumentExtraction"]] = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan"
    )

class DocumentVersion(FullBaseModel):
    """
    Tracks re-uploads or corrected versions of a document.
    """
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    document: Mapped["Document"] = relationship("Document", back_populates="versions")
    uploaded_by: Mapped["User"] = relationship("User")

class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class DocumentExtraction(FullBaseModel):
    """
    Stores extracted data, confidence scores, and raw OCR output.
    """
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    document_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_version.id", ondelete="SET NULL"),
        nullable=True
    )
    
    extraction_engine: Mapped[str] = mapped_column(String(100), nullable=False)
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        String(50), 
        default=ExtractionStatus.PENDING, 
        nullable=False
    )
    
    raw_ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_fields_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    confidence_scores_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    document: Mapped["Document"] = relationship("Document", back_populates="extractions")
