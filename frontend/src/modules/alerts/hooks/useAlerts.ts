import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertApi } from '../../../api/alerts'
import type { AlertFilters, BulkAcknowledgeRequest } from '../../../api/alerts'

export const alertKeys = {
  all: ['alerts'] as const,
  list: (filters: AlertFilters) => [...alertKeys.all, 'list', filters] as const,
  detail: (id: string) => [...alertKeys.all, 'detail', id] as const,
}

export function useAlerts(filters: AlertFilters = {}) {
  return useQuery({
    queryKey: alertKeys.list(filters),
    queryFn: () => alertApi.listAlerts(filters),
    staleTime: 30_000,
  })
}

export function useAlert(id: string) {
  return useQuery({
    queryKey: alertKeys.detail(id),
    queryFn: () => alertApi.getAlert(id),
    enabled: Boolean(id),
    staleTime: 30_000,
  })
}

export function useAcknowledgeAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => alertApi.acknowledgeAlert(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: alertKeys.all })
    },
  })
}

export function useResolveAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => alertApi.resolveAlert(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: alertKeys.all })
    },
  })
}

export function useBulkAcknowledgeAlerts() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: BulkAcknowledgeRequest) => alertApi.bulkAcknowledge(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: alertKeys.all })
    },
  })
}
