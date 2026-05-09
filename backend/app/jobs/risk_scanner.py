"""
Operational Risk Scanner Jobs
================================
Three APScheduler jobs that evaluate entity-level operational risk and persist
append-only RiskAssessment records via RiskEngineService.

Design rules (mirrors alert_scanner.py):
- SQL-native queries only for entity selection — no Python-side aggregation.
- Decimal-safe: all financial comparisons use Decimal literals.
- Per-org sessions: each tenant gets an isolated transaction.
  A failure for one org is logged and skipped; other orgs continue.
- Tenant ContextVar: set via set_tenant_id / reset_tenant_id before calling
  RiskEngineService so apply_tenant_scope() works in background context.
- Deduplication: RiskEngineService.generate_risk_assessment() returns None
  for entities assessed within the dedup window — no extra work in scanner.
- Storm protection: at most _MAX_ASSESSMENTS_PER_SCAN entities assessed
  per job run per org.

This job MUST NOT mutate workflows, alert states, or any operational state.
It appends risk intelligence only.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import reset_tenant_id, set_tenant_id
from app.db.session import SessionLocal
from app.models.invoice import Invoice, InvoiceStatus
from app.models.organization import Organization
from app.models.payment import Payment, PaymentStatus
from app.models.vendor import Vendor, VendorStatus
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.models.risk_assessment import RiskEntityType
from app.services.risk_engine import (
    RiskEngineService,
    INVOICE_DEDUP_MINUTES,
    VENDOR_DEDUP_MINUTES,
    SETTLEMENT_DEDUP_MINUTES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable limits
# ---------------------------------------------------------------------------

# Maximum entities assessed per scan cycle per org.
# If the cap is reached the scan logs a warning; remaining entities are
# deferred to the next cycle.  Prevents runaway assessment storms on large orgs.
_MAX_ASSESSMENTS_PER_SCAN: int = 500

# Unsettled threshold: only RECEIVED payments older than this are assessed
# for settlement risk.  Mirrors the alert scanner's _UNSETTLED_LIABILITY_DAYS.
_SETTLEMENT_RISK_DAYS: int = 1


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

async def _get_active_org_ids() -> List[uuid.UUID]:
    """Fetch IDs of all active tenants in a short-lived read session."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Organization.id).where(Organization.is_active.is_(True))
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Invoice risk scan — every 6 hours
# ---------------------------------------------------------------------------

async def _assess_invoices_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Select all DRAFT/ISSUED invoices for an org and generate risk assessments.

    Ordering: most overdue invoices first, then by outstanding amount descending.
    This ensures the highest-risk entities are assessed when the cap is hit.
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

    query = (
        select(Invoice.id)
        .where(
            Invoice.organization_id == org_id,
            Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
            Invoice.is_deleted.is_(False),
        )
        # Prioritise most overdue then highest outstanding amount
        .order_by(
            func.coalesce(
                func.cast(today, Invoice.due_date.type) - Invoice.due_date,
                0,
            ).desc(),
            outstanding_expr.desc(),
        )
        .limit(_MAX_ASSESSMENTS_PER_SCAN + 1)
    )

    rows = (await session.execute(query)).all()
    capped = len(rows) > _MAX_ASSESSMENTS_PER_SCAN
    if capped:
        rows = rows[:_MAX_ASSESSMENTS_PER_SCAN]
        logger.warning(
            "RISK_SCAN_CAP reached during invoice risk scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ASSESSMENTS_PER_SCAN,
        )

    svc = RiskEngineService(db=session)
    created = 0

    for (inv_id,) in rows:
        assessment = await svc.generate_risk_assessment(
            organization_id=org_id,
            entity_type=RiskEntityType.INVOICE,
            entity_id=inv_id,
            dedup_minutes=INVOICE_DEDUP_MINUTES,
        )
        if assessment is not None:
            created += 1

    return created


async def scan_invoice_risk() -> None:
    """APScheduler job — runs every 6 hours."""
    logger.info("Starting invoice risk scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _assess_invoices_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Invoice risk scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Invoice risk scan complete — %d new assessments", total_created)


# ---------------------------------------------------------------------------
# Vendor risk scan — every 12 hours
# ---------------------------------------------------------------------------

async def _assess_vendors_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Select all ACTIVE vendors for an org and generate risk assessments.

    Vendor count per org is typically small; no ordering priority needed.
    """
    query = (
        select(Vendor.id)
        .where(
            Vendor.organization_id == org_id,
            Vendor.is_deleted.is_(False),
            Vendor.status == VendorStatus.ACTIVE,
        )
        .limit(_MAX_ASSESSMENTS_PER_SCAN + 1)
    )

    rows = (await session.execute(query)).all()
    capped = len(rows) > _MAX_ASSESSMENTS_PER_SCAN
    if capped:
        rows = rows[:_MAX_ASSESSMENTS_PER_SCAN]
        logger.warning(
            "RISK_SCAN_CAP reached during vendor risk scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ASSESSMENTS_PER_SCAN,
        )

    svc = RiskEngineService(db=session)
    created = 0

    for (vendor_id,) in rows:
        assessment = await svc.generate_risk_assessment(
            organization_id=org_id,
            entity_type=RiskEntityType.VENDOR,
            entity_id=vendor_id,
            dedup_minutes=VENDOR_DEDUP_MINUTES,
        )
        if assessment is not None:
            created += 1

    return created


async def scan_vendor_risk() -> None:
    """APScheduler job — runs every 12 hours."""
    logger.info("Starting vendor risk scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _assess_vendors_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Vendor risk scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Vendor risk scan complete — %d new assessments", total_created)


# ---------------------------------------------------------------------------
# Settlement (payment) risk scan — every 12 hours
# ---------------------------------------------------------------------------

async def _assess_settlements_for_org(session: AsyncSession, org_id: uuid.UUID) -> int:
    """
    Select RECEIVED payments with pending settlement balance and generate
    risk assessments.

    Only payments older than _SETTLEMENT_RISK_DAYS are assessed — avoids
    noise from freshly received payments that haven't had time to be settled.

    Ordered by payment_date ascending (oldest first → highest risk first).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_SETTLEMENT_RISK_DAYS)

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

    query = (
        select(Payment.id)
        .where(
            Payment.organization_id == org_id,
            Payment.status == PaymentStatus.RECEIVED,
            Payment.is_deleted.is_(False),
            Payment.payment_date < cutoff,
            unsettled_expr > Decimal("0"),
        )
        .order_by(Payment.payment_date.asc())  # oldest first = highest aging risk
        .limit(_MAX_ASSESSMENTS_PER_SCAN + 1)
    )

    rows = (await session.execute(query)).all()
    capped = len(rows) > _MAX_ASSESSMENTS_PER_SCAN
    if capped:
        rows = rows[:_MAX_ASSESSMENTS_PER_SCAN]
        logger.warning(
            "RISK_SCAN_CAP reached during settlement risk scan: org=%s cap=%d "
            "— remaining entities deferred to next cycle.",
            org_id, _MAX_ASSESSMENTS_PER_SCAN,
        )

    svc = RiskEngineService(db=session)
    created = 0

    for (payment_id,) in rows:
        assessment = await svc.generate_risk_assessment(
            organization_id=org_id,
            entity_type=RiskEntityType.PAYMENT,
            entity_id=payment_id,
            dedup_minutes=SETTLEMENT_DEDUP_MINUTES,
        )
        if assessment is not None:
            created += 1

    return created


async def scan_settlement_risk() -> None:
    """APScheduler job — runs every 12 hours."""
    logger.info("Starting settlement risk scan")
    org_ids = await _get_active_org_ids()
    total_created = 0

    for org_id in org_ids:
        token = set_tenant_id(org_id)
        try:
            async with SessionLocal() as session:
                try:
                    count = await _assess_settlements_for_org(session, org_id)
                    await session.commit()
                    total_created += count
                except Exception:
                    await session.rollback()
                    raise
        except Exception as exc:
            logger.error("Settlement risk scan failed for org %s: %s", org_id, exc)
        finally:
            reset_tenant_id(token)

    logger.info("Settlement risk scan complete — %d new assessments", total_created)
