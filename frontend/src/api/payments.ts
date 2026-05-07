import { get, post, patch } from './client'
import type { Payment, PaymentStatus, PaymentMethod } from '../types'

export interface PaymentListParams {
  invoiceId?: string
  status?: PaymentStatus
  page?: number
  limit?: number
}

export interface PaginatedPayments {
  items: Payment[]
  total: number
  page: number
  limit: number
}

export interface CreatePaymentPayload {
  invoice_id: string
  payment_reference: string
  amount: number
  payment_method: PaymentMethod
  payment_date?: string
  notes?: string
}

export const paymentsApi = {
  list: (params?: PaymentListParams) =>
    get<PaginatedPayments>('/payments', { params }),

  get: (id: string) =>
    get<Payment>(`/payments/${id}`),

  create: (data: CreatePaymentPayload) =>
    post<Payment>('/payments', data),

  updateStatus: (id: string, status: PaymentStatus) =>
    patch<Payment>(`/payments/${id}/status`, { status }),
}
