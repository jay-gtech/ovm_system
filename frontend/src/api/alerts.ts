import { get, patch, post } from './client'
import type { BackendAlert, BackendAlertList } from '../types'

export interface AlertFilters {
  skip?: number
  limit?: number
  status?: string
  severity?: string
  alert_type?: string
  entity_type?: string
  entity_id?: string
  triggered_after?: string
  triggered_before?: string
}

export interface BulkAcknowledgeRequest {
  severity?: string
  alert_type?: string
}

export interface BulkAcknowledgeResponse {
  acknowledged_count: number
}

export const alertApi = {
  listAlerts: (filters: AlertFilters = {}): Promise<BackendAlertList> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        params.append(k, String(v))
      }
    })
    const qs = params.toString()
    return get<BackendAlertList>(`/alerts${qs ? `?${qs}` : ''}`)
  },

  getAlert: (id: string): Promise<BackendAlert> =>
    get<BackendAlert>(`/alerts/${id}`),

  acknowledgeAlert: (id: string): Promise<BackendAlert> =>
    patch<BackendAlert>(`/alerts/${id}/acknowledge`),

  resolveAlert: (id: string): Promise<BackendAlert> =>
    patch<BackendAlert>(`/alerts/${id}/resolve`),

  /**
   * Acknowledge ALL open alerts for the current tenant in one server-side
   * transaction.  Optional filters narrow by severity and/or alert_type.
   * Safer than N individual PATCH calls — pagination-independent and atomic.
   */
  bulkAcknowledge: (body: BulkAcknowledgeRequest = {}): Promise<BulkAcknowledgeResponse> =>
    post<BulkAcknowledgeResponse>('/alerts/bulk-acknowledge', body),
}
