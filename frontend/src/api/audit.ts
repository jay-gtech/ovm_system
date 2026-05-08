import { get } from './client'
import type { AuditLogList } from '../types'

export interface AuditEntityParams {
  skip?: number
  limit?: number
}

export interface AuditSearchParams {
  entity_type?: string
  action?: string
  actor_user_id?: string
  date_from?: string
  date_to?: string
  skip?: number
  limit?: number
}

export const auditApi = {
  getEntityHistory: (entityType: string, entityId: string, params?: AuditEntityParams) =>
    get<AuditLogList>(`/audit/entity/${entityType}/${entityId}`, { params }),

  search: (params?: AuditSearchParams) =>
    get<AuditLogList>('/audit/search', { params }),
}
