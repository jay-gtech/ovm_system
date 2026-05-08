import { useQuery } from '@tanstack/react-query'
import { auditApi } from '../api/audit'
import type { AuditEntityParams } from '../api/audit'

export const auditKeys = {
  all: ['audit'] as const,
  entity: (entityType: string, entityId: string, params?: AuditEntityParams) =>
    [...auditKeys.all, 'entity', entityType, entityId, params] as const,
}

export function useAuditTimeline(
  entityType: string,
  entityId: string,
  params?: AuditEntityParams,
) {
  return useQuery({
    queryKey: auditKeys.entity(entityType, entityId, params),
    queryFn: () => auditApi.getEntityHistory(entityType, entityId, params),
    enabled: !!entityId && !!entityType,
  })
}
