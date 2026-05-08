import uuid
from decimal import Decimal
from typing import Sequence, Tuple
from datetime import datetime, timezone
from app.services.base import BaseService
from app.services.audit import AuditService
from app.models.payment import Payment, PaymentStatus
from app.models.invoice import InvoiceStatus
from app.schemas.payment import PaymentCreate
from app.services.uow import BaseUnitOfWork
from app.services.exceptions import (
    NotFoundDomainError,
    ValidationDomainError,
)

# Maps terminal payment status values to their canonical audit action names
_PAYMENT_STATUS_ACTIONS = {
    PaymentStatus.RECEIVED: "PAYMENT_RECEIVED",
    PaymentStatus.FAILED: "PAYMENT_FAILED",
    PaymentStatus.CANCELLED: "PAYMENT_CANCELLED",
}


class PaymentService(BaseService):
    def __init__(self, uow: BaseUnitOfWork):
        super().__init__(uow)  # AS-1: do not pass uow.payments as audit_hook

    async def create_payment(
        self, obj_in: PaymentCreate
    ) -> Payment:
        """
        Create a new payment for an invoice.

        Financial Rules:
        - Invoice must exist, belong to the same tenant, and be in ISSUED status.
        - New payments are always created as PENDING; status can only be advanced
          via update_status(). This prevents client-side payment state injection.
        """
        async with self.uow:
            # 1. Validate Invoice exists and belongs to current tenant
            invoice = await self.uow.invoices.get(self.uow.session, obj_in.invoice_id)
            if not invoice:
                raise NotFoundDomainError(f"Invoice {obj_in.invoice_id} not found.")

            # 2. WF-2: Only ISSUED invoices can receive new payments
            if invoice.status not in (InvoiceStatus.ISSUED,):
                raise ValidationDomainError(
                    f"Cannot create payment for invoice in status '{invoice.status.value}'. "
                    "Invoice must be in ISSUED status."
                )

            payment_data = obj_in.model_dump()
            # SEC-3: Status is always server-assigned to PENDING at creation.
            payment_data["status"] = PaymentStatus.PENDING
            if not payment_data.get("payment_date"):
                payment_data["payment_date"] = datetime.now(timezone.utc)

            # 3. Create Payment (repository flush makes payment.id available)
            payment = await self.uow.payments.create(
                self.uow.session,
                obj_in=payment_data
            )

            await AuditService.log_event(
                self.uow.session,
                entity_type="payment",
                entity_id=payment.id,
                action="PAYMENT_CREATED",
                metadata={
                    "invoice_id": str(payment.invoice_id),
                    "amount": str(payment.amount),
                    "payment_method": payment.payment_method.value,
                    "payment_reference": payment.payment_reference,
                },
            )

            await self.uow.commit()
            return payment

    async def update_status(
        self, payment_id: uuid.UUID, status: PaymentStatus
    ) -> Payment:
        """
        Update payment status with financial validation and invoice consistency.

        Transition rules:
        - PENDING → RECEIVED: validates overpayment; auto-marks invoice PAID if fully paid.
        - RECEIVED → FAILED/CANCELLED: rolls invoice back from PAID to ISSUED if applicable.
        - Idempotent: no-op if status is unchanged.
        """
        async with self.uow:
            payment = await self.uow.payments.get(self.uow.session, payment_id)
            if not payment:
                raise NotFoundDomainError(f"Payment {payment_id} not found.")

            if payment.status == status:
                return payment

            old_status = payment.status

            if status == PaymentStatus.RECEIVED:
                # Validate overpayment — current_received is already Decimal from repository
                invoice = await self.uow.invoices.get(self.uow.session, payment.invoice_id)
                current_received = await self.uow.payments.get_received_sum_by_invoice(
                    self.uow.session, payment.invoice_id
                )

                total_received = current_received + payment.amount
                if total_received > invoice.total_amount:
                    raise ValidationDomainError(
                        f"Payment of {payment.amount} would cause overpayment. "
                        f"Invoice total: {invoice.total_amount}, "
                        f"Current received: {current_received}"
                    )

                # If fully paid, mark invoice as PAID
                if total_received == invoice.total_amount:
                    await self.uow.invoices.update(
                        self.uow.session,
                        db_obj=invoice,
                        obj_in={"status": InvoiceStatus.PAID}
                    )

            # WF-1: Reversing a RECEIVED payment must roll back invoice PAID status.
            elif old_status == PaymentStatus.RECEIVED and status in (
                PaymentStatus.FAILED, PaymentStatus.CANCELLED
            ):
                invoice = await self.uow.invoices.get(self.uow.session, payment.invoice_id)
                current_received = await self.uow.payments.get_received_sum_by_invoice(
                    self.uow.session, payment.invoice_id
                )
                new_received = current_received - payment.amount
                if new_received < invoice.total_amount and invoice.status == InvoiceStatus.PAID:
                    await self.uow.invoices.update(
                        self.uow.session,
                        db_obj=invoice,
                        obj_in={"status": InvoiceStatus.ISSUED}
                    )

            payment = await self.uow.payments.update(
                self.uow.session,
                db_obj=payment,
                obj_in={"status": status}
            )

            action = _PAYMENT_STATUS_ACTIONS.get(status, "PAYMENT_STATUS_CHANGED")
            await AuditService.log_event(
                self.uow.session,
                entity_type="payment",
                entity_id=payment.id,
                action=action,
                field_name="status",
                old_value=old_status.value,
                new_value=status.value,
            )

            await self.uow.commit()
            return payment

    async def get_invoice_payment_summary(
        self, invoice_id: uuid.UUID
    ) -> Tuple[Decimal, Decimal]:
        """
        Compute (paid_amount, outstanding_amount) for an invoice.
        Returns Decimal values — no float conversion.
        """
        async with self.uow:
            invoice = await self.uow.invoices.get(self.uow.session, invoice_id)
            if not invoice:
                raise NotFoundDomainError(f"Invoice {invoice_id} not found.")

            paid_amount = await self.uow.payments.get_received_sum_by_invoice(
                self.uow.session, invoice_id
            )
            outstanding_amount = invoice.total_amount - paid_amount

            return paid_amount, outstanding_amount

    async def get_by_invoice(
        self, invoice_id: uuid.UUID
    ) -> Sequence[Payment]:
        """List all payments for an invoice (tenant-scoped via repository)."""
        async with self.uow:
            return await self.uow.payments.get_by_invoice(self.uow.session, invoice_id)

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment:
        """
        Fetch a single payment by ID (tenant-scoped via BaseRepository.get).
        AS-1: explicit method required since BaseService does not store a repository.
        """
        async with self.uow:
            payment = await self.uow.payments.get(self.uow.session, payment_id)
            if not payment:
                raise NotFoundDomainError(f"Payment {payment_id} not found.")
            return payment

    async def get_multi(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[Payment]:
        """List payments for the current tenant with pagination."""
        async with self.uow:
            return await self.uow.payments.get_multi(
                self.uow.session, skip=skip, limit=limit
            )
