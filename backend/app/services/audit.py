import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_tenant_id, get_user_id
from app.models.audit_log import AuditLog


def _safe_str(value: Any) -> Optional[str]:
    """Serialize any scalar value to a string safe for audit storage."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


def _safe_json(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively convert a dict to be JSON-safe, handling Decimal and UUID."""
    if data is None:
        return None
    result: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, Decimal):
            result[k] = str(v)
        elif isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif isinstance(v, dict):
            result[k] = _safe_json(v)
        elif isinstance(v, list):
            result[k] = [_safe_str(i) if not isinstance(i, dict) else _safe_json(i) for i in v]
        else:
            result[k] = v
    return result


class AuditService:
    """
    Centralized immutable audit logging service.

    All writes are performed via static methods so the service requires no
    instantiation — any service layer can call AuditService.log_event() directly.

    Transaction contract:
    - session.add() is called but NOT session.flush() or session.commit().
    - The calling service layer is responsible for committing the transaction.
    - If the main operation rolls back, the audit log rolls back with it (atomic).
    """

    @staticmethod
    async def log_event(
        session: AsyncSession,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_user_id: Optional[uuid.UUID] = None,
        actor_role: Optional[str] = None,
        field_name: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append an immutable audit record to the current database transaction.

        - Automatically resolves tenant_id from the active ContextVar.
        - Automatically resolves actor_user_id from the active ContextVar if not provided.
        - Handles Decimal and UUID serialization for old_value / new_value.
        - Handles Decimal and UUID serialization within metadata dict.
        - Best-effort: silently no-ops if tenant context is missing (should not happen
          in normal request flow, but guards against background task edge cases).
        """
        tenant_id = get_tenant_id()
        if not tenant_id:
            return

        resolved_actor = actor_user_id if actor_user_id is not None else get_user_id()

        log = AuditLog(
            organization_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=resolved_actor,
            actor_role=actor_role,
            field_name=field_name,
            old_value=_safe_str(old_value),
            new_value=_safe_str(new_value),
            reason=reason,
            metadata_json=_safe_json(metadata),
        )
        session.add(log)


# ---------------------------------------------------------------------------
# Legacy hook interface — retained so BaseService.record_audit() still compiles.
# No new code should use these; use AuditService.log_event() directly instead.
# ---------------------------------------------------------------------------

class AuditEvent:
    """Structured data representing a domain event to be audited (legacy)."""

    def __init__(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        from datetime import datetime, timezone
        from app.core.context import get_request_id

        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.payload = payload or {}
        self.metadata = metadata or {}
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


from abc import ABC, abstractmethod  # noqa: E402


class AuditHook(ABC):
    """Interface for audit logging hooks (legacy)."""

    @abstractmethod
    async def record(self, event: AuditEvent) -> None:
        pass


class NoOpAuditHook(AuditHook):
    """Default no-op hook used by BaseService when no real hook is wired."""

    async def record(self, event: AuditEvent) -> None:
        pass
