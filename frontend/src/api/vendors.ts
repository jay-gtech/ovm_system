import apiClient, { get, post } from './client'
import type { Vendor, VendorStatus } from '../types'

// Backend response shape (snake_case)
export interface BackendVendor {
  id: string
  organization_id: string
  vendor_code: string
  legal_name: string
  display_name: string
  tax_id: string | null
  email: string | null
  phone: string | null
  address: string | null
  notes: string | null
  status: VendorStatus
  created_at: string
  updated_at: string
}

export interface BackendPaginatedVendors {
  items: BackendVendor[]
  total: number
}

// Backend uses skip+limit, not page+limit
export interface VendorListParams {
  skip?: number
  limit?: number
  status?: VendorStatus
}

export interface VendorCreatePayload {
  vendor_code: string
  legal_name: string
  display_name: string
  tax_id?: string
  email?: string
  phone?: string
  address?: string
  notes?: string
}

export interface VendorUpdatePayload {
  legal_name?: string
  display_name?: string
  tax_id?: string
  email?: string
  phone?: string
  address?: string
  notes?: string
}

function normalizeVendor(raw: BackendVendor): Vendor {
  return {
    id: raw.id,
    vendor_code: raw.vendor_code,
    legal_name: raw.legal_name,
    name: raw.display_name,
    gstin: raw.tax_id ?? '',
    pan: '',
    email: raw.email ?? '',
    phone: raw.phone ?? '',
    city: raw.address ?? '',
    status: raw.status,
    // Analytics fields not available from backend yet
    reliabilityScore: 0,
    totalOrders: 0,
    totalValue: 0,
    onTimeDeliveryRate: 0,
    createdAt: raw.created_at,
  }
}

export const vendorsApi = {
  list: async (params?: VendorListParams): Promise<{ items: Vendor[]; total: number }> => {
    const raw = await get<BackendPaginatedVendors>('/vendors', { params })
    return { items: raw.items.map(normalizeVendor), total: raw.total }
  },

  get: async (id: string): Promise<Vendor> => {
    const raw = await get<BackendVendor>(`/vendors/${id}`)
    return normalizeVendor(raw)
  },

  create: async (data: VendorCreatePayload): Promise<Vendor> => {
    const raw = await post<BackendVendor>('/vendors', data)
    return normalizeVendor(raw)
  },

  // Backend uses PATCH, not PUT
  update: async (id: string, data: VendorUpdatePayload): Promise<Vendor> => {
    const { data: raw } = await apiClient.patch<BackendVendor>(`/vendors/${id}`, data)
    return normalizeVendor(raw)
  },

  // No DELETE endpoint — deactivate sets status to INACTIVE
  deactivate: async (id: string): Promise<Vendor> => {
    const { data: raw } = await apiClient.patch<BackendVendor>(`/vendors/${id}/status`, { status: 'INACTIVE' })
    return normalizeVendor(raw)
  },

  updateStatus: async (id: string, status: VendorStatus): Promise<Vendor> => {
    const { data: raw } = await apiClient.patch<BackendVendor>(`/vendors/${id}/status`, { status })
    return normalizeVendor(raw)
  },
}
