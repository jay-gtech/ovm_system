import logging
from typing import Generic, TypeVar, Optional, Any
from app.services.uow import SQLAlchemyUnitOfWork
from app.services.audit import AuditHook, NoOpAuditHook, AuditEvent
from app.core.context import get_request_id, get_tenant_id

logger = logging.getLogger(__name__)

class BaseService:
    """
    Base class for all application services.
    Provides shared infrastructure for:
    - Transaction management via Unit of Work
    - Audit logging hooks
    - Structured logging context
    - Domain exception mapping
    """

    def __init__(
        self, 
        uow: SQLAlchemyUnitOfWork, 
        audit_hook: AuditHook = NoOpAuditHook()
    ):
        self.uow = uow
        self.audit_hook = audit_hook

    @property
    def log_context(self) -> dict:
        """Returns standard logging context for the current request."""
        return {
            "request_id": str(get_request_id()) if get_request_id() else None,
            "tenant_id": str(get_tenant_id()) if get_tenant_id() else None,
            "service": self.__class__.__name__
        }

    def log_info(self, msg: str, **kwargs):
        """Log info message with request/tenant context."""
        logger.info(msg, extra={"extra": {**self.log_context, **kwargs}})

    def log_error(self, msg: str, **kwargs):
        """Log error message with request/tenant context."""
        logger.error(msg, extra={"extra": {**self.log_context, **kwargs}})

    async def record_audit(
        self, 
        action: str, 
        resource_type: str, 
        resource_id: Optional[str] = None,
        payload: Optional[dict] = None,
        metadata: Optional[dict] = None
    ):
        """Record a domain event for auditing."""
        event = AuditEvent(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            metadata=metadata
        )
        await self.audit_hook.record(event)
