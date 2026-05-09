import { get } from './client'
import type {
  RiskAssessmentList,
  RiskAssessment,
  RiskSummary,
} from '../types'

export interface RiskAssessmentFilters {
  skip?: number
  limit?: number
  entity_type?: string
  entity_id?: string
  risk_level?: string
  generated_after?: string
  generated_before?: string
  latest_only?: boolean
}

export const riskAssessmentsApi = {
  listAssessments: (filters: RiskAssessmentFilters = {}): Promise<RiskAssessmentList> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        params.append(k, String(v))
      }
    })
    const qs = params.toString()
    return get<RiskAssessmentList>(`/risk-assessments${qs ? `?${qs}` : ''}`)
  },

  getAssessment: (id: string): Promise<RiskAssessment> =>
    get<RiskAssessment>(`/risk-assessments/${id}`),

  getEntityHistory: (entityType: string, entityId: string, limit = 30): Promise<RiskAssessmentList> =>
    get<RiskAssessmentList>(
      `/risk-assessments/entity/${entityType}/${entityId}?limit=${limit}`
    ),

  getSummary: (): Promise<RiskSummary> =>
    get<RiskSummary>('/risk-assessments/summary'),
}
