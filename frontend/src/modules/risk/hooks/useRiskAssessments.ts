import { useQuery } from '@tanstack/react-query'
import { riskAssessmentsApi } from '../../../api/riskAssessments'
import type { RiskAssessmentFilters } from '../../../api/riskAssessments'

export const riskKeys = {
  all: ['risk-assessments'] as const,
  summary: () => [...riskKeys.all, 'summary'] as const,
  list: (filters: RiskAssessmentFilters) => [...riskKeys.all, 'list', filters] as const,
  detail: (id: string) => [...riskKeys.all, 'detail', id] as const,
  entityHistory: (entityType: string, entityId: string) =>
    [...riskKeys.all, 'history', entityType, entityId] as const,
}

export function useRiskSummary() {
  return useQuery({
    queryKey: riskKeys.summary(),
    queryFn: () => riskAssessmentsApi.getSummary(),
    staleTime: 5 * 60_000, // 5 min — refreshed by scheduler every 6–12 h
  })
}

export function useRiskAssessments(filters: RiskAssessmentFilters = {}) {
  return useQuery({
    queryKey: riskKeys.list(filters),
    queryFn: () => riskAssessmentsApi.listAssessments(filters),
    staleTime: 5 * 60_000,
  })
}

export function useRiskAssessment(id: string) {
  return useQuery({
    queryKey: riskKeys.detail(id),
    queryFn: () => riskAssessmentsApi.getAssessment(id),
    enabled: Boolean(id),
    staleTime: 5 * 60_000,
  })
}

export function useEntityRiskHistory(entityType: string, entityId: string) {
  return useQuery({
    queryKey: riskKeys.entityHistory(entityType, entityId),
    queryFn: () => riskAssessmentsApi.getEntityHistory(entityType, entityId),
    enabled: Boolean(entityType) && Boolean(entityId),
    staleTime: 5 * 60_000,
  })
}
