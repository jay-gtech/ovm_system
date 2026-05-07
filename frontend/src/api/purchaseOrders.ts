import { get, post, put } from './client'
import type { Order, OrderStatus } from '../types'

export interface PurchaseOrderListParams {
  search?: string
  status?: OrderStatus
  vendorId?: string
  page?: number
  limit?: number
}

export interface PaginatedOrders {
  items: Order[]
  total: number
  page: number
  limit: number
}

export interface CreateOrderPayload {
  vendorId: string
  description: string
  quantity: number
  unitPrice: number
  expectedDelivery: string
  notes?: string
}

export const purchaseOrdersApi = {
  list: (params?: PurchaseOrderListParams) =>
    get<PaginatedOrders>('/purchase-orders', { params }),

  get: (id: string) =>
    get<Order>(`/purchase-orders/${id}`),

  create: (data: CreateOrderPayload) =>
    post<Order>('/purchase-orders', data),

  update: (id: string, data: Partial<CreateOrderPayload>) =>
    put<Order>(`/purchase-orders/${id}`, data),

  updateStatus: (id: string, status: OrderStatus) =>
    put<Order>(`/purchase-orders/${id}/status`, { status }),
}
