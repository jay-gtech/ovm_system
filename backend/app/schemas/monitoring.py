import uuid
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict

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
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    aging_days: int
    is_overdue: bool
    vendor: VendorLinkage
    
    model_config = ConfigDict(from_attributes=True)

class PendingPaymentResponse(BaseModel):
    id: uuid.UUID
    payment_reference: str
    amount: Decimal
    status: str
    aging_days: int
    invoice: InvoiceLinkage
    vendor: VendorLinkage
    
    model_config = ConfigDict(from_attributes=True)

class UnsettledPaymentResponse(BaseModel):
    id: uuid.UUID
    payment_reference: str
    amount: Decimal
    settlement_total: Decimal
    unsettled_amount: Decimal
    invoice: InvoiceLinkage
    vendor: VendorLinkage
    
    model_config = ConfigDict(from_attributes=True)

class PendingSettlementResponse(BaseModel):
    id: uuid.UUID
    settlement_reference: str
    amount: Decimal
    status: str
    aging_days: int
    vendor: VendorLinkage
    invoice: InvoiceLinkage
    
    model_config = ConfigDict(from_attributes=True)

class FinancialSummaryResponse(BaseModel):
    total_outstanding_invoices: Decimal
    total_pending_payments: Decimal
    total_unsettled_liabilities: Decimal
    total_pending_settlements: Decimal
    
    model_config = ConfigDict(from_attributes=True)
