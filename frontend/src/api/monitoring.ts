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
  total_amount: number
  paid_amount: number
  outstanding_amount: number
  aging_days: number
  is_overdue: boolean
  vendor: VendorLinkage
}

export interface PendingPaymentResponse {
  id: string
  payment_reference: string
  amount: number
  status: string
  aging_days: number
  invoice: InvoiceLinkage
  vendor: VendorLinkage
}

export interface UnsettledPaymentResponse {
  id: string
  payment_reference: string
  amount: number
  settlement_total: number
  unsettled_amount: number
  invoice: InvoiceLinkage
  vendor: VendorLinkage
}

export interface PendingSettlementResponse {
  id: string
  settlement_reference: string
  amount: number
  status: string
  aging_days: number
  vendor: VendorLinkage
  invoice: InvoiceLinkage
}

export interface FinancialSummaryResponse {
  total_outstanding_invoices: number
  total_pending_payments: number
  total_unsettled_liabilities: number
  total_pending_settlements: number
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
