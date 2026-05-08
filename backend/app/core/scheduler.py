import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

# Singleton scheduler — started in main.py startup, shut down on shutdown.
scheduler = AsyncIOScheduler(timezone="UTC")


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
