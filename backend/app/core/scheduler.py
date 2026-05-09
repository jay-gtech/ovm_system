import logging
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_SUBMITTED
from app.services.metrics import metrics

logger = logging.getLogger(__name__)

# Singleton scheduler — started in main.py startup, shut down on shutdown.
scheduler = AsyncIOScheduler(timezone="UTC")

# Dictionary to track job start times
_job_starts = {}

def _scheduler_listener(event):
    job_id = event.job_id
    
    if event.code == EVENT_JOB_SUBMITTED:
        _job_starts[job_id] = time.time()
        logger.info(f"Scheduler job '{job_id}' started", extra={"service": "scheduler", "operation": job_id, "status": "started"})
        
    elif event.code == EVENT_JOB_EXECUTED:
        start_time = _job_starts.pop(job_id, time.time())
        duration_ms = (time.time() - start_time) * 1000
        
        metrics.inc("job_success_total")
        metrics.observe("job_latency_sum", "job_count", duration_ms)
        
        logger.info(f"Scheduler job '{job_id}' completed successfully in {duration_ms:.2f}ms", 
                    extra={"service": "scheduler", "operation": job_id, "status": "success", "duration_ms": duration_ms})
        
    elif event.code == EVENT_JOB_ERROR:
        start_time = _job_starts.pop(job_id, time.time())
        duration_ms = (time.time() - start_time) * 1000
        
        metrics.inc("job_failure_total")
        metrics.observe("job_latency_sum", "job_count", duration_ms)
        
        logger.error(f"Scheduler job '{job_id}' failed: {str(event.exception)}", 
                     exc_info=event.exception,
                     extra={"service": "scheduler", "operation": job_id, "status": "error", "duration_ms": duration_ms, "error_type": type(event.exception).__name__ if event.exception else "Unknown"})
                     
    elif event.code == EVENT_JOB_MISSED:
        metrics.inc("job_skipped_total")
        logger.warning(f"Scheduler job '{job_id}' missed its execution window", 
                       extra={"service": "scheduler", "operation": job_id, "status": "missed"})

# Attach listener
scheduler.add_listener(_scheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_SUBMITTED)

def setup_scheduler() -> None:
    """
    Register all background operational alert scanning jobs.

    Intervals follow the sprint spec:
      - Overdue invoice scan        → every 1 hour
      - Unsettled liability scan    → every 1 hour
      - Workflow stall scan         → every 6 hours
      - High financial exposure     → every 1 hour

    replace_existing=True is safe for repeated startup calls (e.g., hot-reload).
    Jobs are lazily imported here to avoid circular imports at module load time.
    """
    from app.jobs.alert_scanner import (
        scan_overdue_invoices,
        scan_unsettled_liabilities,
        scan_workflow_stalls,
        scan_high_exposure,
    )
    from app.jobs.sla_scanner import scan_sla_evaluations
    from app.jobs.risk_scanner import (
        scan_invoice_risk,
        scan_vendor_risk,
        scan_settlement_risk,
    )

    scheduler.add_job(
        scan_invoice_risk,
        trigger="interval",
        hours=6,
        id="invoice_risk_scan",
        replace_existing=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scan_vendor_risk,
        trigger="interval",
        hours=12,
        id="vendor_risk_scan",
        replace_existing=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scan_settlement_risk,
        trigger="interval",
        hours=12,
        id="settlement_risk_scan",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.add_job(
        scan_overdue_invoices,
        trigger="interval",
        hours=1,
        id="overdue_invoice_scan",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        scan_unsettled_liabilities,
        trigger="interval",
        hours=1,
        id="unsettled_liability_scan",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        scan_workflow_stalls,
        trigger="interval",
        hours=6,
        id="workflow_stall_scan",
        replace_existing=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scan_high_exposure,
        trigger="interval",
        hours=1,
        id="high_exposure_scan",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        scan_sla_evaluations,
        trigger="interval",
        minutes=15,
        id="sla_evaluation_scan",
        replace_existing=True,
        misfire_grace_time=120,
    )

    logger.info(
        "Scheduler configured: overdue(1h), unsettled(1h), stall(6h), "
        "exposure(1h), sla_eval(15m)"
    )
