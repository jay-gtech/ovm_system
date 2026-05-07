import { get, post, put } from './client'
import type { Invoice, InvoiceStatus } from '../types'

export interface InvoiceListParams {
  search?: string
  status?: InvoiceStatus
  vendorId?: string
  orderId?: string
  isOverdue?: boolean
  page?: number
  limit?: number
}

export interface PaginatedInvoices {
  items: Invoice[]
  total: number
  page: number
  limit: number
}

export interface CreateInvoicePayload {
  orderId: string
  amount: number
  taxAmount: number
  dueDate: string
  notes?: string
}

export const invoicesApi = {
  list: (params?: InvoiceListParams) =>
    get<PaginatedInvoices>('/invoices', { params }),

  get: (id: string) =>
    get<Invoice>(`/invoices/${id}`),

  create: (data: CreateInvoicePayload) =>
    post<Invoice>('/invoices', data),

  updateStatus: (id: string, status: InvoiceStatus) =>
    put<Invoice>(`/invoices/${id}/status`, { status }),
}
