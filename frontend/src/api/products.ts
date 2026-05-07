import apiClient, { get, post } from './client'

export type ProductStatus = 'ACTIVE' | 'INACTIVE'

// Backend response shape (snake_case, from FastAPI)
export interface BackendProduct {
  id: string
  organization_id: string
  sku: string
  name: string
  description: string | null
  category: string | null
  unit_price: string | number   // Decimal may serialize as string or number
  currency: string
  vendor_id: string | null
  notes: string | null
  status: ProductStatus
  created_at: string
  updated_at: string
}

export interface BackendProductListResponse {
  items: BackendProduct[]
  total: number
  skip: number
  limit: number
}

// Normalized frontend shape
export interface Product {
  id: string
  sku: string
  name: string
  description?: string
  category?: string
  unitPrice: number
  currency: string
  vendor_id?: string
  notes?: string
  status: ProductStatus
  tenantId?: string
  createdAt: string
  updatedAt?: string
}

// Backend uses skip+limit, not page+limit
export interface ProductListParams {
  skip?: number
  limit?: number
}

export interface ProductCreatePayload {
  sku: string
  name: string
  description?: string
  category?: string
  unit_price: number
  currency?: string
  vendor_id?: string
  notes?: string
}

export interface ProductUpdatePayload {
  name?: string
  description?: string
  category?: string
  unit_price?: number
  currency?: string
  vendor_id?: string | null   // null clears the vendor association
  notes?: string
}

function normalizeProduct(raw: BackendProduct): Product {
  return {
    id: raw.id,
    sku: raw.sku,
    name: raw.name,
    description: raw.description ?? undefined,
    category: raw.category ?? undefined,
    unitPrice: Number(raw.unit_price),
    currency: raw.currency,
    vendor_id: raw.vendor_id ?? undefined,
    notes: raw.notes ?? undefined,
    status: raw.status,
    tenantId: raw.organization_id,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  }
}

export const productsApi = {
  list: async (params?: ProductListParams): Promise<{ items: Product[]; total: number }> => {
    const raw = await get<BackendProductListResponse>('/products', { params })
    return { items: raw.items.map(normalizeProduct), total: raw.total }
  },

  get: async (id: string): Promise<Product> => {
    const raw = await get<BackendProduct>(`/products/${id}`)
    return normalizeProduct(raw)
  },

  create: async (data: ProductCreatePayload): Promise<Product> => {
    const raw = await post<BackendProduct>('/products', data)
    return normalizeProduct(raw)
  },

  // Backend uses PATCH, not PUT; SKU is immutable and ignored on update
  update: async (id: string, data: ProductUpdatePayload): Promise<Product> => {
    const { data: raw } = await apiClient.patch<BackendProduct>(`/products/${id}`, data)
    return normalizeProduct(raw)
  },

  // No DELETE endpoint — backend uses soft-delete via status lifecycle
  setStatus: async (id: string, status: ProductStatus): Promise<Product> => {
    const { data: raw } = await apiClient.patch<BackendProduct>(`/products/${id}/status`, { status })
    return normalizeProduct(raw)
  },

  activate:   (id: string) => productsApi.setStatus(id, 'ACTIVE'),
  deactivate: (id: string) => productsApi.setStatus(id, 'INACTIVE'),
}
