import threading
from typing import Dict, Any

class MetricsRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        
        # System Metrics
        self.api_requests_total = 0
        self.api_errors_total = 0
        self.api_latency_sum = 0.0
        self.db_query_latency_sum = 0.0
        self.db_query_count = 0

        # Workflow Metrics
        self.alerts_generated_total = 0
        self.sla_breaches_total = 0
        self.notifications_sent_total = 0
        self.risk_assessments_total = 0

        # IDP Metrics
        self.ocr_success_total = 0
        self.ocr_failure_total = 0
        self.ocr_latency_sum = 0.0
        self.ocr_count = 0
        self.validation_mismatch_total = 0
        self.approval_count = 0
        self.rejection_count = 0

        # Scheduler Metrics
        self.job_success_total = 0
        self.job_failure_total = 0
        self.job_latency_sum = 0.0
        self.job_count = 0
        self.job_retry_total = 0
        self.job_skipped_total = 0

    def inc(self, metric_name: str, value: int = 1):
        with self._lock:
            current = getattr(self, metric_name, 0)
            setattr(self, metric_name, current + value)

    def observe(self, metric_name_sum: str, metric_name_count: str, value: float):
        with self._lock:
            current_sum = getattr(self, metric_name_sum, 0.0)
            current_count = getattr(self, metric_name_count, 0)
            setattr(self, metric_name_sum, current_sum + value)
            setattr(self, metric_name_count, current_count + 1)

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "system": {
                    "api_requests_total": self.api_requests_total,
                    "api_errors_total": self.api_errors_total,
                    "avg_api_latency_ms": self.api_latency_sum / self.api_requests_total if self.api_requests_total > 0 else 0,
                    "avg_db_latency_ms": self.db_query_latency_sum / self.db_query_count if self.db_query_count > 0 else 0,
                },
                "workflow": {
                    "alerts_generated_total": self.alerts_generated_total,
                    "sla_breaches_total": self.sla_breaches_total,
                    "notifications_sent_total": self.notifications_sent_total,
                    "risk_assessments_total": self.risk_assessments_total,
                },
                "idp": {
                    "ocr_success_rate": (self.ocr_success_total / self.ocr_count * 100) if self.ocr_count > 0 else 0,
                    "ocr_failure_rate": (self.ocr_failure_total / self.ocr_count * 100) if self.ocr_count > 0 else 0,
                    "avg_ocr_latency_ms": self.ocr_latency_sum / self.ocr_count if self.ocr_count > 0 else 0,
                    "validation_mismatch_rate": (self.validation_mismatch_total / self.ocr_count * 100) if self.ocr_count > 0 else 0,
                    "approvals": self.approval_count,
                    "rejections": self.rejection_count,
                },
                "scheduler": {
                    "job_success_total": self.job_success_total,
                    "job_failure_total": self.job_failure_total,
                    "avg_job_latency_ms": self.job_latency_sum / self.job_count if self.job_count > 0 else 0,
                    "job_retry_total": self.job_retry_total,
                    "job_skipped_total": self.job_skipped_total,
                }
            }

# Global singleton
metrics = MetricsRegistry()
