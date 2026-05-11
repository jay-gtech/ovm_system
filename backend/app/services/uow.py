from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.vendor import VendorRepository
from app.repositories.product import ProductRepository
from app.repositories.purchase_order import PurchaseOrderRepository, POLineItemRepository
from app.repositories.invoice import InvoiceRepository, InvoiceLineItemRepository
from app.repositories.payment import PaymentRepository
from app.repositories.vendor_settlement import VendorSettlementRepository
from app.repositories.audit import AuditRepository
from app.repositories.alert import AlertRepository
from app.repositories.sla_policy import SLAPolicyRepository
from app.repositories.notification import NotificationRepository
from app.repositories.document import DocumentRepository, DocumentExtractionRepository, DocumentValidationRepository
from app.repositories.risk_assessment import RiskAssessmentRepository


class BaseUnitOfWork(ABC):
    """
    Abstract Base Class for the Unit of Work pattern.

    Transaction contract (financial-system rule):
      - Commit is ALWAYS explicit in the service layer via uow.commit().
      - __aexit__ is a safety-net ONLY: it rolls back on exception.
      - __aexit__ never auto-commits on success — this prevents double-commit
        when services (correctly) call commit() before the context exits.
    """

    session: AsyncSession
    organizations: OrganizationRepository
    users: UserRepository
    vendors: VendorRepository
    products: ProductRepository
    purchase_orders: PurchaseOrderRepository
    po_line_items: POLineItemRepository
    invoices: InvoiceRepository
    invoice_line_items: InvoiceLineItemRepository
    payments: PaymentRepository
    vendor_settlements: VendorSettlementRepository
    audit_logs: AuditRepository
    alerts: AlertRepository
    sla_policies: SLAPolicyRepository
    notifications: NotificationRepository
    documents: DocumentRepository
    document_extractions: DocumentExtractionRepository
    document_validations: DocumentValidationRepository
    risk_assessments: RiskAssessmentRepository

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Safety-net rollback only.
        On exception  → rollback (best-effort; original exception is re-raised).
        On success    → no-op; service layer already called commit().
        """
        if exc_type is not None:
            try:
                await self.rollback()
            except Exception:
                # Rollback failure is logged by the caller's exception handler.
                # We intentionally do NOT swallow the original exception.
                pass

    @abstractmethod
    async def commit(self) -> None:
        """Persist the current transaction to the database."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all pending changes in the current transaction."""
        pass


class SQLAlchemyUnitOfWork(BaseUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    Session ownership rules:
      - If a session is injected (FastAPI DI path), this UoW does NOT close it.
        Session lifecycle is owned by get_db().
      - If no session is injected (background tasks, standalone use), this UoW
        creates and closes its own session.
    """

    def __init__(self, session: AsyncSession = None):
        self._session_factory = SessionLocal
        self._provided_session = session
        self.session = session
        self.organizations = OrganizationRepository()
        self.users = UserRepository()
        self.vendors = VendorRepository()
        self.products = ProductRepository()
        self.purchase_orders = PurchaseOrderRepository()
        self.po_line_items = POLineItemRepository()
        self.invoices = InvoiceRepository()
        self.invoice_line_items = InvoiceLineItemRepository()
        self.payments = PaymentRepository()
        self.vendor_settlements = VendorSettlementRepository()
        self.audit_logs = AuditRepository()
        self.alerts = AlertRepository()
        self.sla_policies = SLAPolicyRepository()
        self.notifications = NotificationRepository()
        self.documents = DocumentRepository()
        self.document_extractions = DocumentExtractionRepository()
        self.document_validations = DocumentValidationRepository()
        self.risk_assessments = RiskAssessmentRepository()

    async def __aenter__(self):
        if self.session is None:
            self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Delegate rollback-only safety-net to base class.
        await super().__aexit__(exc_type, exc_val, exc_tb)
        # Only close sessions that this UoW created; never close an injected session.
        if self._provided_session is None and self.session is not None:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
