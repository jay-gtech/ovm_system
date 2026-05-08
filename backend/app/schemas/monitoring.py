import uuid
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, PlainSerializer
from typing_extensions import Annotated

DecimalStr = Annotated[Decimal, PlainSerializer(lambda x: str(x) if x is not None else None, return_type=str, when_used='json')]

class VendorLinkage(BaseModel):
    id: uuid.UUID
    vendor_code: str
    legal_name: str

    model_config = ConfigDict(from_attributes=True)

class InvoiceLinkage(BaseModel):
    id: uuid.UUID
    invoice_number: str

    model_config = ConfigDict(from_attributes=True)

class OutstandingInvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    status: str
    total_amount: DecimalStr
    paid_amount: DecimalStr
    outstanding_amount: DecimalStr
    aging_days: int
    is_overdue: bool
    vendor: VendorLinkage

    model_config = ConfigDict(from_attributes=True)

class PendingPaymentResponse(BaseModel):
    id: uuid.UUID
    payment_reference: str
    amount: DecimalStr
    status: str
    aging_days: int
    invoice: InvoiceLinkage
    vendor: VendorLinkage

    model_config = ConfigDict(from_attributes=True)

class UnsettledPaymentResponse(BaseModel):
    id: uuid.UUID
    payment_reference: str
    amount: DecimalStr
    settlement_total: DecimalStr
    unsettled_amount: DecimalStr
    invoice: InvoiceLinkage
    vendor: VendorLinkage

    model_config = ConfigDict(from_attributes=True)

class PendingSettlementResponse(BaseModel):
    id: uuid.UUID
    settlement_reference: str
    amount: DecimalStr
    status: str
    aging_days: int
    vendor: VendorLinkage
    invoice: InvoiceLinkage

    model_config = ConfigDict(from_attributes=True)

class FinancialSummaryResponse(BaseModel):
    total_outstanding_invoices: DecimalStr
    total_pending_payments: DecimalStr
    total_unsettled_liabilities: DecimalStr
    total_pending_settlements: DecimalStr

    model_config = ConfigDict(from_attributes=True)
