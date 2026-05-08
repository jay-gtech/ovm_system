import uuid
from typing import Sequence
from datetime import datetime, timezone

from app.services.base import BaseService
from app.services.audit import AuditService
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.models.payment import PaymentStatus
from app.schemas.vendor_settlement import VendorSettlementCreate
from app.services.uow import BaseUnitOfWork
from app.services.exceptions import (
    NotFoundDomainError,
    ValidationDomainError,
    ConflictDomainError,
)

# Maps terminal settlement status values to their canonical audit action names
_SETTLEMENT_STATUS_ACTIONS = {
    SettlementStatus.SETTLED: "SETTLEMENT_COMPLETED",
    SettlementStatus.CANCELLED: "SETTLEMENT_CANCELLED",
}


class VendorSettlementService(BaseService):
    def __init__(self, uow: BaseUnitOfWork):
        super().__init__(uow)

    async def create_settlement(
        self, obj_in: VendorSettlementCreate, organization_id: uuid.UUID
    ) -> VendorSettlement:
        async with self.uow:
            # 1. Check uniqueness of settlement_reference per organization
            existing = await self.uow.vendor_settlements.get_by_reference(
                self.uow.session, organization_id, obj_in.settlement_reference
            )
            if existing:
                raise ConflictDomainError(
                    f"Settlement reference {obj_in.settlement_reference} already exists for this organization."
                )

            # 2. Check if Payment exists and is RECEIVED
            payment = await self.uow.payments.get(self.uow.session, obj_in.payment_id)
            if not payment:
                raise NotFoundDomainError(f"Payment {obj_in.payment_id} not found.")

            if payment.status != PaymentStatus.RECEIVED:
                raise ValidationDomainError(
                    f"Only RECEIVED payments may be settled. Current payment status is {payment.status}."
                )

            # 3. Validation: Settlement amount must never exceed linked payment received amount
            current_settled = await self.uow.vendor_settlements.get_settled_sum_by_payment(
                self.uow.session, obj_in.payment_id
            )
            total_settlement = current_settled + obj_in.amount
            if total_settlement > payment.amount:
                raise ValidationDomainError(
                    f"Settlement amount ({obj_in.amount}) plus existing settlements ({current_settled}) "
                    f"exceeds payment amount ({payment.amount})."
                )

            # Check if invoice matches
            if payment.invoice_id != obj_in.invoice_id:
                raise ValidationDomainError("Payment does not belong to the specified invoice.")

            settlement_data = obj_in.model_dump()
            settlement_data["status"] = SettlementStatus.PENDING
            if not settlement_data.get("settlement_date"):
                settlement_data["settlement_date"] = datetime.now(timezone.utc)

            settlement = await self.uow.vendor_settlements.create(
                self.uow.session, obj_in=settlement_data
            )

            await AuditService.log_event(
                self.uow.session,
                entity_type="settlement",
                entity_id=settlement.id,
                action="SETTLEMENT_CREATED",
                metadata={
                    "vendor_id": str(settlement.vendor_id),
                    "invoice_id": str(settlement.invoice_id),
                    "payment_id": str(settlement.payment_id),
                    "amount": str(settlement.amount),
                    "settlement_reference": settlement.settlement_reference,
                },
            )

            await self.uow.commit()
            return settlement

    async def get_by_id(self, settlement_id: uuid.UUID) -> VendorSettlement:
        async with self.uow:
            settlement = await self.uow.vendor_settlements.get(self.uow.session, settlement_id)
            if not settlement:
                raise NotFoundDomainError(f"Settlement {settlement_id} not found.")
            return settlement

    async def update_status(
        self, settlement_id: uuid.UUID, status: SettlementStatus
    ) -> VendorSettlement:
        async with self.uow:
            settlement = await self.uow.vendor_settlements.get(self.uow.session, settlement_id)
            if not settlement:
                raise NotFoundDomainError(f"Settlement {settlement_id} not found.")

            if settlement.status == status:
                return settlement

            old_status = settlement.status

            # When changing to SETTLED, re-validate the underlying payment
            if status == SettlementStatus.SETTLED:
                payment = await self.uow.payments.get(self.uow.session, settlement.payment_id)
                if not payment or payment.status != PaymentStatus.RECEIVED:
                    raise ValidationDomainError("Underlying payment is no longer RECEIVED.")

            settlement = await self.uow.vendor_settlements.update(
                self.uow.session, db_obj=settlement, obj_in={"status": status}
            )

            action = _SETTLEMENT_STATUS_ACTIONS.get(status, "SETTLEMENT_STATUS_CHANGED")
            await AuditService.log_event(
                self.uow.session,
                entity_type="settlement",
                entity_id=settlement.id,
                action=action,
                field_name="status",
                old_value=old_status.value,
                new_value=status.value,
                metadata={
                    "vendor_id": str(settlement.vendor_id),
                    "amount": str(settlement.amount),
                },
            )

            await self.uow.commit()
            return settlement

    async def get_multi(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[VendorSettlement]:
        async with self.uow:
            return await self.uow.vendor_settlements.get_multi(
                self.uow.session, skip=skip, limit=limit
            )
