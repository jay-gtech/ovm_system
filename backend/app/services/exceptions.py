from typing import Any, Optional


class DomainError(Exception):
    """Base class for all domain-related exceptions."""

    def __init__(
        self, 
        message: str, 
        code: str = "DOMAIN_ERROR", 
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ValidationDomainError(DomainError):
    """Raised when domain validation rules are violated."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class ConflictDomainError(DomainError):
    """Raised when a domain operation conflicts with the current state (e.g. unique constraint)."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="CONFLICT_ERROR", details=details)


class AuthorizationDomainError(DomainError):
    """Raised when a domain operation violates authorization rules."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="AUTHORIZATION_ERROR", details=details)


class TenantIsolationError(DomainError):
    """Raised when a cross-tenant operation is detected or tenant context is missing."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="TENANT_ISOLATION_ERROR", details=details)


class NotFoundDomainError(DomainError):
    """Raised when a requested domain entity is not found."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="NOT_FOUND_ERROR", details=details)
