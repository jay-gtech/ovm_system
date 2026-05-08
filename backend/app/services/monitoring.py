from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.tenancy import apply_tenant_scope
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.models.vendor import Vendor
from app.schemas.monitoring import (
    OutstandingInvoiceResponse,
    PendingPaymentResponse,
    UnsettledPaymentResponse,
    PendingSettlementResponse,
    FinancialSummaryResponse,
    VendorLinkage,
    InvoiceLinkage
)

class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _calculate_aging_days(self, created_at: datetime) -> int:
        now = datetime.now(timezone.utc)
        return (now - created_at).days

    async def get_outstanding_invoices(self) -> List[OutstandingInvoiceResponse]:
        query = select(Invoice).options(
            selectinload(Invoice.vendor),
            selectinload(Invoice.payments)
        ).where(Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]))
        query = apply_tenant_scope(query, Invoice)
        query = query.where(
            Invoice.is_deleted.is_(False),
            Invoice.outstanding_amount > 0
        )
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        response = []
        for inv in invoices:
            aging_days = self._calculate_aging_days(inv.created_at)
            is_overdue = aging_days > 30  # Assuming standard 30-day terms for monitoring
            
            response.append(OutstandingInvoiceResponse(
                id=inv.id,
                invoice_number=inv.invoice_number,
                status=inv.status,
                total_amount=inv.total_amount,
                paid_amount=inv.paid_amount,
                outstanding_amount=inv.outstanding_amount,
                aging_days=aging_days,
                is_overdue=is_overdue,
                vendor=VendorLinkage(
                    id=inv.vendor.id,
                    vendor_code=inv.vendor.vendor_code,
                    legal_name=inv.vendor.legal_name
                )
            ))
        return response

    async def get_pending_payments(self) -> List[PendingPaymentResponse]:
        query = select(Payment).options(
            selectinload(Payment.invoice).selectinload(Invoice.vendor)
        ).where(Payment.status == PaymentStatus.PENDING)
        query = apply_tenant_scope(query, Payment)
        query = query.where(Payment.is_deleted.is_(False))
        
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        response = []
        for p in payments:
            aging_days = self._calculate_aging_days(p.created_at)
            response.append(PendingPaymentResponse(
                id=p.id,
                payment_reference=p.payment_reference,
                amount=p.amount,
                status=p.status,
                aging_days=aging_days,
                invoice=InvoiceLinkage(
                    id=p.invoice.id,
                    invoice_number=p.invoice.invoice_number
                ),
                vendor=VendorLinkage(
                    id=p.invoice.vendor.id,
                    vendor_code=p.invoice.vendor.vendor_code,
                    legal_name=p.invoice.vendor.legal_name
                )
            ))
        return response

    async def get_unsettled_payments(self) -> List[UnsettledPaymentResponse]:
        # A payment is unsettled if it is RECEIVED but its amount > sum of associated settlements
        settled_subq = select(
            VendorSettlement.payment_id,
            func.sum(VendorSettlement.amount).label('settled_amount')
        ).where(
            VendorSettlement.status == SettlementStatus.SETTLED,
            VendorSettlement.is_deleted.is_(False)
        )
        settled_subq = apply_tenant_scope(settled_subq, VendorSettlement)
        settled_subq = settled_subq.group_by(VendorSettlement.payment_id).subquery()

        query = select(
            Payment,
            func.coalesce(settled_subq.c.settled_amount, Decimal("0.0000")).label('settled_sum')
        ).outerjoin(
            settled_subq, Payment.id == settled_subq.c.payment_id
        ).options(
            selectinload(Payment.invoice).selectinload(Invoice.vendor)
        ).where(
            Payment.status == PaymentStatus.RECEIVED,
            Payment.is_deleted.is_(False)
        )
        query = apply_tenant_scope(query, Payment)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        response = []
        for p, settled_sum in rows:
            if settled_sum < p.amount:
                response.append(UnsettledPaymentResponse(
                    id=p.id,
                    payment_reference=p.payment_reference,
                    amount=p.amount,
                    settlement_total=settled_sum,
                    unsettled_amount=p.amount - settled_sum,
                    invoice=InvoiceLinkage(
                        id=p.invoice.id,
                        invoice_number=p.invoice.invoice_number
                    ),
                    vendor=VendorLinkage(
                        id=p.invoice.vendor.id,
                        vendor_code=p.invoice.vendor.vendor_code,
                        legal_name=p.invoice.vendor.legal_name
                    )
                ))
        return response

    async def get_pending_settlements(self) -> List[PendingSettlementResponse]:
        query = select(VendorSettlement).options(
            selectinload(VendorSettlement.vendor),
            selectinload(VendorSettlement.invoice)
        ).where(VendorSettlement.status == SettlementStatus.PENDING)
        query = apply_tenant_scope(query, VendorSettlement)
        query = query.where(VendorSettlement.is_deleted.is_(False))
        
        result = await self.db.execute(query)
        settlements = result.scalars().all()
        
        response = []
        for s in settlements:
            aging_days = self._calculate_aging_days(s.created_at)
            response.append(PendingSettlementResponse(
                id=s.id,
                settlement_reference=s.settlement_reference,
                amount=s.amount,
                status=s.status,
                aging_days=aging_days,
                vendor=VendorLinkage(
                    id=s.vendor.id,
                    vendor_code=s.vendor.vendor_code,
                    legal_name=s.vendor.legal_name
                ),
                invoice=InvoiceLinkage(
                    id=s.invoice.id,
                    invoice_number=s.invoice.invoice_number
                )
            ))
        return response

    async def get_financial_summary(self) -> FinancialSummaryResponse:
        inv_query = select(func.sum(Invoice.outstanding_amount)).where(
            Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
            Invoice.outstanding_amount > 0,
            Invoice.is_deleted.is_(False)
        )
        inv_query = apply_tenant_scope(inv_query, Invoice)
        inv_sum = (await self.db.execute(inv_query)).scalar() or Decimal("0.0000")

        pay_query = select(func.sum(Payment.amount)).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.is_deleted.is_(False)
        )
        pay_query = apply_tenant_scope(pay_query, Payment)
        pay_sum = (await self.db.execute(pay_query)).scalar() or Decimal("0.0000")

        settle_query = select(func.sum(VendorSettlement.amount)).where(
            VendorSettlement.status == SettlementStatus.PENDING,
            VendorSettlement.is_deleted.is_(False)
        )
        settle_query = apply_tenant_scope(settle_query, VendorSettlement)
        settle_sum = (await self.db.execute(settle_query)).scalar() or Decimal("0.0000")

        settled_subq = select(
            VendorSettlement.payment_id,
            func.sum(VendorSettlement.amount).label('settled_amount')
        ).where(
            VendorSettlement.status == SettlementStatus.SETTLED,
            VendorSettlement.is_deleted.is_(False)
        )
        settled_subq = apply_tenant_scope(settled_subq, VendorSettlement)
        settled_subq = settled_subq.group_by(VendorSettlement.payment_id).subquery()

        unsettled_query = select(
            func.sum(Payment.amount - func.coalesce(settled_subq.c.settled_amount, Decimal("0.0000")))
        ).outerjoin(
            settled_subq, Payment.id == settled_subq.c.payment_id
        ).where(
            Payment.status == PaymentStatus.RECEIVED,
            Payment.is_deleted.is_(False),
            Payment.amount > func.coalesce(settled_subq.c.settled_amount, Decimal("0.0000"))
        )
        unsettled_query = apply_tenant_scope(unsettled_query, Payment)
        unsettled_sum = (await self.db.execute(unsettled_query)).scalar() or Decimal("0.0000")

        return FinancialSummaryResponse(
            total_outstanding_invoices=inv_sum,
            total_pending_payments=pay_sum,
            total_unsettled_liabilities=unsettled_sum,
            total_pending_settlements=settle_sum
        )
