from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base

class OperationalError(Base):
    """
    Centralized operational error tracking.
    Captures: OCR failures, scheduler failures, validation exceptions,
    notification failures, extraction failures.
    """
    __tablename__ = "operational_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String, index=True, nullable=False) # e.g., 'ocr', 'scheduler', 'notification'
    operation = Column(String, nullable=False)           # e.g., 'extract_invoice', 'scan_overdue'
    error_type = Column(String, index=True, nullable=False)
    stack_trace = Column(Text, nullable=True)            # Truncated stack trace
    
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=True) # None for system-wide errors
    request_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    
    retryable = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
