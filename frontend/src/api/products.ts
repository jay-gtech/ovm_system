import { get, post, put, del } from './client'

export interface Product {
  id: string
  name: string
  sku: string
  description?: string
  unit: string
  unitPrice: number
  category?: string
  isActive: boolean
  tenantId?: string
  createdAt: string
  updatedAt?: string
}

export interface ProductListParams {
  search?: string
  category?: string
  isActive?: boolean
  page?: number
  limit?: number
}

export interface PaginatedProducts {
  items: Product[]
  total: number
  page: number
  limit: number
}

export const productsApi = {
  list: (params?: ProductListParams) =>
    get<PaginatedProducts>('/products', { params }),

  get: (id: string) =>
    get<Product>(`/products/${id}`),

  create: (data: Partial<Product>) =>
    post<Product>('/products', data),

  update: (id: string, data: Partial<Product>) =>
    put<Product>(`/products/${id}`, data),

  remove: (id: string) =>
    del<void>(`/products/${id}`),
}
