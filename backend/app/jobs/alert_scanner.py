"""
Operational Alert Scanner Jobs
================================
Four APScheduler jobs that scan financial workflow state and create
operational alerts via AlertService.

Design rules:
- SQL-native queries only — no Python-side aggregation loops.
- Decimal-safe: all thresholds use Decimal literals.
- Per-org sessions: each tenant gets an isolated transaction.
  A failure for one org is logged and skipped; other orgs continue.
- Tenant ContextVar: set via set_tenant_id / reset_tenant_id before
  calling AlertService so apply_tenant_scope() works in background context.
- Deduplication: AlertService.create_alert() returns None for duplicates;
  no extra work is done by the scanner.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import set_tenant_id, reset_tenant_id
from app.db.session import SessionLocal
from app.models.alert import AlertSeverity, AlertType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.organization import Organization
from app.models.payment import Payment, PaymentStatus
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.services.alert import AlertService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable thresholds (module-level constants).
# Replace with settings fields if tenant-level customisation is required later.
# ---------------------------------------------------------------------------

# OVERDUE_INVOICE: outstanding amount above this triggers HIGH instead of MEDIUM.
_OVERDUE_HIGH_AMOUNT: Decimal = Decimal("100000")

# UNSETTLED_VENDOR_LIABILITY: days since payment was RECEIVED before alerting.
_UNSETTLED_LIABILITY_DAYS: int = 7

# WORKFLOW_STALL: invoice age (days) with no active payment activity.
_WORKFLOW_STALL_DAYS: int = 14

# HIGH_FINANCIAL_EXPOSURE: outstanding amount above which CRITICAL alert fires.
_HIGH_EXPOSURE_AMOUNT: Decimal = Decimal("500000")

# ALERT STORM PROTECTION: maximum alerts created per scan cycle per org.
# Prevents mass-insert under large overdue/exposure datasets.  If the cap is
# reached the scan logs a structured warning and stops.  Remaining entities
# will be picked up on the next scheduled run once prior alerts are resolved.
_MAX_ALERTS_PER_SCAN: int = 500


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_active_org_ids() -> List[uuid.UUID]:
    """Fetch IDs of all active tenants in a short-lived read session."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Organization.id).where(Organization.is_active.is_(True))
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Task 5 — Overdue Invoice Alert
# ---------------------------------------------------------------------------

async def _overdue_scan_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Find invoices that are past due_date with outstanding_amount > 0.

    Query is SQL-native: paid amount computed via scalar subquery.
    Returns the number of new alerts created.
    """
    today = datetime.now(timezone.utc).date()

    paid_subq = (
        select(func.coalesce(func.sum(Payment.amount), Decimal("0.0000")))
        .where(
            Payment.invoice_id == Invoice.id,
            Payment.status == PaymentStatus.RECEIVED,
            Payment.is_deleted.is_(False),
        )
        .scalar_subquery()
    )

    outstanding_expr = Invoice.total_amount - paid_subq

    query = select(
        Invoice.id,
        Invoice.invoice_number,
        Invoice.total_amount,
        outstanding_expr.label("outstanding_amount"),
    ).where(
        Invoice.organization_id == org_id,
        Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
        Invoice.is_deleted.is_(False),
        Invoice.due_date < today,
        outstanding_expr > Decimal("0"),
    )

    # Fetch one extra row to detect whether the cap would be exceeded.
    query = query.limit(_MAX_ALERTS_PER_SCAN + 1)
    rows = (await session.execute(query)).all()

    capped = len(rows) > _MAX_ALERTS_PER_SCAN
    if capped:
        rows = rows[:_MAX_ALERTS_PER_SCAN]
        logger.warning(
            "ALERT_STORM_CAP reached during overdue scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ALERTS_PER_SCAN,
        )

    svc = AlertService(db=session)
    created = 0

    for row in rows:
        inv_id, inv_number, total, outstanding = row
        outstanding = Decimal(str(outstanding))
        severity = (
            AlertSeverity.HIGH if outstanding >= _OVERDUE_HIGH_AMOUNT
            else AlertSeverity.MEDIUM
        )
        alert = await svc.create_alert(
            organization_id=org_id,
            alert_type=AlertType.OVERDUE_INVOICE,
            severity=severity,
            entity_type="invoice",
            entity_id=inv_id,
            title=f"Overdue Invoice: {inv_number}",
            message=(
                f"Invoice {inv_number} is overdue with "
                f"₹{outstanding:,.2f} outstanding."
            ),
            metadata={"invoice_number": inv_number, "outstanding_amount": outstanding},
        )
        if alert is not None:
            created += 1

    return created


async def scan_overdue_invoices() -> None:
    """APScheduler job — runs every 1 hour."""
    logger.info("Starting overdue invoice scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _overdue_scan_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Overdue scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Overdue invoice scan complete — %d new alerts", total_created)


# ---------------------------------------------------------------------------
# Task 6 — Unsettled Vendor Liability Alert
# ---------------------------------------------------------------------------

async def _unsettled_scan_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Find RECEIVED payments whose settled amount < payment amount after threshold days.

    Uses a settled-amount scalar subquery so no Python-side aggregation occurs.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_UNSETTLED_LIABILITY_DAYS)

    settled_subq = (
        select(func.coalesce(func.sum(VendorSettlement.amount), Decimal("0.0000")))
        .where(
            VendorSettlement.payment_id == Payment.id,
            VendorSettlement.status == SettlementStatus.SETTLED,
            VendorSettlement.is_deleted.is_(False),
        )
        .scalar_subquery()
    )

    unsettled_expr = Payment.amount - settled_subq

    query = select(
        Payment.id,
        Payment.payment_reference,
        Payment.amount,
        unsettled_expr.label("unsettled_amount"),
    ).where(
        Payment.organization_id == org_id,
        Payment.status == PaymentStatus.RECEIVED,
        Payment.is_deleted.is_(False),
        Payment.payment_date < cutoff,
        unsettled_expr > Decimal("0"),
    )

    query = query.limit(_MAX_ALERTS_PER_SCAN + 1)
    rows = (await session.execute(query)).all()

    if len(rows) > _MAX_ALERTS_PER_SCAN:
        rows = rows[:_MAX_ALERTS_PER_SCAN]
        logger.warning(
            "ALERT_STORM_CAP reached during unsettled scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ALERTS_PER_SCAN,
        )

    svc = AlertService(db=session)
    created = 0

    for row in rows:
        pay_id, pay_ref, amount, unsettled = row
        unsettled = Decimal(str(unsettled))
        alert = await svc.create_alert(
            organization_id=org_id,
            alert_type=AlertType.UNSETTLED_VENDOR_LIABILITY,
            severity=AlertSeverity.HIGH,
            entity_type="payment",
            entity_id=pay_id,
            title=f"Unsettled Vendor Liability: {pay_ref}",
            message=(
                f"Payment {pay_ref} was received but ₹{unsettled:,.2f} "
                f"remains unsettled after {_UNSETTLED_LIABILITY_DAYS} days."
            ),
            metadata={
                "payment_reference": pay_ref,
                "unsettled_amount": unsettled,
                "threshold_days": _UNSETTLED_LIABILITY_DAYS,
            },
        )
        if alert is not None:
            created += 1

    return created


async def scan_unsettled_liabilities() -> None:
    """APScheduler job — runs every 1 hour."""
    logger.info("Starting unsettled liability scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _unsettled_scan_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Unsettled liability scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Unsettled liability scan complete — %d new alerts", total_created)


# ---------------------------------------------------------------------------
# Task 7 — Workflow Stall Detection
# ---------------------------------------------------------------------------

async def _stall_scan_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Detect invoices in DRAFT/ISSUED with no active payment activity for X days.

    "Active payment" means a payment that is not FAILED or CANCELLED and was
    created within the stall window — avoids false positives from failed attempts.
    The invoice itself must be older than the stall window (no false positives on
    freshly created invoices).
    """
    now = datetime.now(timezone.utc)
    stall_cutoff = now - timedelta(days=_WORKFLOW_STALL_DAYS)

    # Exists check: any non-terminal payment for this invoice created recently.
    recent_payment_exists = (
        select(Payment.id)
        .where(
            Payment.invoice_id == Invoice.id,
            Payment.status.notin_([PaymentStatus.FAILED, PaymentStatus.CANCELLED]),
            Payment.is_deleted.is_(False),
            Payment.created_at > stall_cutoff,
        )
        .exists()
    )

    query = select(
        Invoice.id,
        Invoice.invoice_number,
        Invoice.total_amount,
    ).where(
        Invoice.organization_id == org_id,
        Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
        Invoice.is_deleted.is_(False),
        Invoice.created_at < stall_cutoff,
        ~recent_payment_exists,
    )

    query = query.limit(_MAX_ALERTS_PER_SCAN + 1)
    rows = (await session.execute(query)).all()

    if len(rows) > _MAX_ALERTS_PER_SCAN:
        rows = rows[:_MAX_ALERTS_PER_SCAN]
        logger.warning(
            "ALERT_STORM_CAP reached during stall scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ALERTS_PER_SCAN,
        )

    svc = AlertService(db=session)
    created = 0

    for row in rows:
        inv_id, inv_number, total = row
        alert = await svc.create_alert(
            organization_id=org_id,
            alert_type=AlertType.WORKFLOW_STALL,
            severity=AlertSeverity.MEDIUM,
            entity_type="invoice",
            entity_id=inv_id,
            title=f"Workflow Stall: {inv_number}",
            message=(
                f"Invoice {inv_number} has had no payment activity "
                f"for {_WORKFLOW_STALL_DAYS} days."
            ),
            metadata={
                "invoice_number": inv_number,
                "stall_threshold_days": _WORKFLOW_STALL_DAYS,
                "total_amount": total,
            },
        )
        if alert is not None:
            created += 1

    return created


async def scan_workflow_stalls() -> None:
    """APScheduler job — runs every 6 hours."""
    logger.info("Starting workflow stall scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _stall_scan_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Workflow stall scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Workflow stall scan complete — %d new alerts", total_created)


# ---------------------------------------------------------------------------
# Task 8 — High Financial Exposure Alert
# ---------------------------------------------------------------------------

async def _exposure_scan_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Detect invoices whose outstanding balance exceeds the critical threshold.

    Uses the same paid-amount scalar subquery pattern as the overdue scan to
    avoid Python-side aggregation.
    """
    paid_subq = (
        select(func.coalesce(func.sum(Payment.amount), Decimal("0.0000")))
        .where(
            Payment.invoice_id == Invoice.id,
            Payment.status == PaymentStatus.RECEIVED,
            Payment.is_deleted.is_(False),
        )
        .scalar_subquery()
    )

    outstanding_expr = Invoice.total_amount - paid_subq

    query = select(
        Invoice.id,
        Invoice.invoice_number,
        Invoice.total_amount,
        outstanding_expr.label("outstanding_amount"),
    ).where(
        Invoice.organization_id == org_id,
        Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
        Invoice.is_deleted.is_(False),
        outstanding_expr >= _HIGH_EXPOSURE_AMOUNT,
    )

    query = query.limit(_MAX_ALERTS_PER_SCAN + 1)
    rows = (await session.execute(query)).all()

    if len(rows) > _MAX_ALERTS_PER_SCAN:
        rows = rows[:_MAX_ALERTS_PER_SCAN]
        logger.warning(
            "ALERT_STORM_CAP reached during exposure scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ALERTS_PER_SCAN,
        )

    svc = AlertService(db=session)
    created = 0

    for row in rows:
        inv_id, inv_number, total, outstanding = row
        outstanding = Decimal(str(outstanding))
        alert = await svc.create_alert(
            organization_id=org_id,
            alert_type=AlertType.HIGH_FINANCIAL_EXPOSURE,
            severity=AlertSeverity.CRITICAL,
            entity_type="invoice",
            entity_id=inv_id,
            title=f"High Financial Exposure: {inv_number}",
            message=(
                f"Invoice {inv_number} carries ₹{outstanding:,.2f} in "
                f"outstanding exposure, exceeding the critical threshold."
            ),
            metadata={
                "invoice_number": inv_number,
                "outstanding_amount": outstanding,
                "exposure_threshold": _HIGH_EXPOSURE_AMOUNT,
            },
        )
        if alert is not None:
            created += 1

    return created


async def scan_high_exposure() -> None:
    """APScheduler job — runs every 1 hour."""
    logger.info("Starting high financial exposure scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _exposure_scan_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("High exposure scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("High exposure scan complete — %d new alerts", total_created)
