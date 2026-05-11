import client from './client';

export interface OpsMetrics {
  system: {
    api_requests_total: number;
    api_errors_total: number;
    avg_api_latency_ms: number;
    avg_db_latency_ms: number;
  };
  workflow: {
    alerts_generated_total: number;
    sla_breaches_total: number;
    notifications_sent_total: number;
    risk_assessments_total: number;
  };
  idp: {
    ocr_success_rate: number;
    ocr_failure_rate: number;
    avg_ocr_latency_ms: number;
    validation_mismatch_rate: number;
    approvals: number;
    rejections: number;
  };
  scheduler: {
    job_success_total: number;
    job_failure_total: number;
    avg_job_latency_ms: number;
    job_retry_total: number;
    job_skipped_total: number;
  };
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run_time: string | null;
  pending: boolean;
}

export interface OperationalError {
  id: string;
  service: string;
  operation: string;
  error_type: string;
  stack_trace: string | null;
  tenant_id: string | null;
  request_id: string | null;
  retryable: boolean;
  retry_count: number;
  created_at: string;
}

export interface HealthDetails {
  metrics: OpsMetrics;
  system_status: string;
  version: string;
}

export const opsApi = {
  getMetrics: () => client.get<OpsMetrics>('/ops/metrics').then(res => res.data),
  getSchedulerJobs: () => client.get<SchedulerJob[]>('/ops/scheduler/jobs').then(res => res.data),
  getRecentErrors: (limit = 50) => client.get<OperationalError[]>('/ops/errors/recent', { params: { limit } }).then(res => res.data),
  getHealthDetails: () => client.get<HealthDetails>('/ops/health/details').then(res => res.data),
};
