import { get } from './client'

export interface VendorLinkage {
  id: string
  vendor_code: string
  legal_name: string
}

export interface InvoiceLinkage {
  id: string
  invoice_number: string
}

export interface OutstandingInvoiceResponse {
  id: string
  invoice_number: string
  status: string
  total_amount: string
  paid_amount: string
  outstanding_amount: string
  aging_days: number
  is_overdue: boolean
  vendor: VendorLinkage
}

export interface PendingPaymentResponse {
  id: string
  payment_reference: string
  amount: string
  status: string
  aging_days: number
  invoice: InvoiceLinkage
  vendor: VendorLinkage
}

export interface UnsettledPaymentResponse {
  id: string
  payment_reference: string
  amount: string
  settlement_total: string
  unsettled_amount: string
  invoice: InvoiceLinkage
  vendor: VendorLinkage
}

export interface PendingSettlementResponse {
  id: string
  settlement_reference: string
  amount: string
  status: string
  aging_days: number
  vendor: VendorLinkage
  invoice: InvoiceLinkage
}

export interface FinancialSummaryResponse {
  total_outstanding_invoices: string
  total_pending_payments: string
  total_unsettled_liabilities: string
  total_pending_settlements: string
}

export const monitoringApi = {
  getOutstandingInvoices: () =>
    get<OutstandingInvoiceResponse[]>('/monitoring/outstanding-invoices'),

  getPendingPayments: () =>
    get<PendingPaymentResponse[]>('/monitoring/pending-payments'),

  getUnsettledPayments: () =>
    get<UnsettledPaymentResponse[]>('/monitoring/unsettled-payments'),

  getPendingSettlements: () =>
    get<PendingSettlementResponse[]>('/monitoring/pending-settlements'),

  getFinancialSummary: () =>
    get<FinancialSummaryResponse>('/monitoring/financial-summary'),
}
