from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone
from app.core.context import get_tenant_id, get_user_id, get_request_id


class AuditEvent:
    """
    Structured data representing a domain event to be audited.
    """
    def __init__(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.payload = payload or {}
        self.metadata = metadata or {}
        
        # Capture context at event creation
        self.tenant_id = get_tenant_id()
        self.user_id = get_user_id()
        self.request_id = get_request_id()
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "request_id": str(self.request_id) if self.request_id else None,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditHook(ABC):
    """
    Interface for audit logging hooks.
    Services can call these hooks to record domain-significant actions.
    """
    @abstractmethod
    async def record(self, event: AuditEvent) -> None:
        """Record an audit event."""
        pass


class NoOpAuditHook(AuditHook):
    """
    Default implementation that does nothing.
    Used when audit logging is disabled or not yet implemented.
    """
    async def record(self, event: AuditEvent) -> None:
        pass
