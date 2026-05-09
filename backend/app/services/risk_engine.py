"""
Risk Engine Service — Deterministic Operational Intelligence

Architecture rules enforced here:
  - MUST NOT mutate workflows, alert statuses, approvals, or any operational state.
  - MUST NOT auto-resolve alerts or bypass human decision-making.
  - Provides read-only intelligence and scoring only — humans remain decision-makers.
  - All scoring logic is deterministic: same inputs always produce the same score.
  - All financial arithmetic uses Decimal — no float.
  - All data aggregation is SQL-native — no Python-side aggregation loops.
  - Configurable weight constants are module-level (no magic numbers inline).
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.models.audit_log import AuditAction
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.risk_assessment import RiskAssessment, RiskEntityType, RiskLevel
from app.models.vendor import Vendor
from app.models.vendor_settlement import VendorSettlement, SettlementStatus
from app.repositories.risk_assessment import RiskAssessmentRepository
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

# =============================================================================
# Configurable weight constants.
# Weights within each category sum to 1.0 (100%).
# Adjust these constants to tune scoring sensitivity without touching logic.
# =============================================================================

# --- Invoice risk factor weights ---
_INV_W_OVERDUE_DAYS: Decimal = Decimal("0.35")
_INV_W_OUTSTANDING:  Decimal = Decimal("0.25")
_INV_W_ALERT_COUNT:  Decimal = Decimal("0.15")
_INV_W_SLA_BREACH:   Decimal = Decimal("0.15")
_INV_W_ESCALATION:   Decimal = Decimal("0.10")

# --- Invoice factor normalisation ceilings (value that yields factor score = 100) ---
_INV_OVERDUE_DAYS_CEIL: int     = 30
_INV_OUTSTANDING_CEIL:  Decimal = Decimal("500000")
_INV_ALERT_CEIL:        int     = 3
_INV_SLA_BREACH_CEIL:   int     = 2
_INV_ESCALATION_CEIL:   int     = 2

# --- Vendor risk factor weights ---
_VEN_W_OVERDUE_RATIO:   Decimal = Decimal("0.35")
_VEN_W_UNRESOLVED_LIAB: Decimal = Decimal("0.30")
_VEN_W_DELAYED_SETTLEM: Decimal = Decimal("0.20")
_VEN_W_SLA_BREACH:      Decimal = Decimal("0.15")

# --- Vendor factor normalisation ceilings ---
_VEN_UNRESOLVED_LIAB_CEIL: int = 5
_VEN_DELAYED_SETTLEM_CEIL: int = 5
_VEN_SLA_BREACH_CEIL:      int = 5

# --- Settlement (payment) risk factor weights ---
_SET_W_AGING_DAYS:    Decimal = Decimal("0.40")
_SET_W_PENDING_AMT:   Decimal = Decimal("0.30")
_SET_W_PARTIAL_COUNT: Decimal = Decimal("0.20")
_SET_W_ALERTS:        Decimal = Decimal("0.10")

# --- Settlement factor normalisation ceilings ---
_SET_AGING_CEIL:    int     = 30
_SET_PENDING_CEIL:  Decimal = Decimal("500000")
_SET_PARTIAL_CEIL:  int     = 5
_SET_ALERTS_CEIL:   int     = 3

# --- Risk level classification thresholds (0–100 scale) ---
_THRESHOLD_MEDIUM:   int = 26
_THRESHOLD_HIGH:     int = 51
_THRESHOLD_CRITICAL: int = 76

# --- Delayed settlement threshold: days after RECEIVED payment before flagging ---
_DELAYED_SETTLEMENT_DAYS: int = 7

# --- Scanner dedup windows: slightly shorter than scan interval to prevent gaps ---
INVOICE_DEDUP_MINUTES:    int = 300   # 5 h window for 6 h scan
VENDOR_DEDUP_MINUTES:     int = 660   # 11 h window for 12 h scan
SETTLEMENT_DEDUP_MINUTES: int = 660   # 11 h window for 12 h scan


# =============================================================================
# Pure scoring helpers — synchronous, no I/O, fully testable in isolation
# =============================================================================

def _normalize(value: int, ceiling: int) -> Decimal:
    """Scale an integer factor value to a 0–100 Decimal score."""
    if ceiling <= 0 or value <= 0:
        return Decimal("0")
    return Decimal(str(min(100, int(value * 100 / ceiling))))


def _normalize_decimal(value: Decimal, ceiling: Decimal) -> Decimal:
    """Scale a Decimal factor value to a 0–100 Decimal score."""
    if ceiling <= 0 or value <= 0:
        return Decimal("0")
    return Decimal(str(min(100, int(value * 100 / ceiling))))


def _clamp_score(weighted_sum: Decimal) -> int:
    """Round and clamp a weighted 0–100 score to an integer in [0, 100]."""
    return max(0, min(100, int(weighted_sum.quantize(Decimal("1"), rounding=ROUND_HALF_UP))))


def _classify_risk(score: int) -> str:
    """Map a 0–100 integer score to a RiskLevel string."""
    if score >= _THRESHOLD_CRITICAL:
        return RiskLevel.CRITICAL
    if score >= _THRESHOLD_HIGH:
        return RiskLevel.HIGH
    if score >= _THRESHOLD_MEDIUM:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _level_to_int(level: str) -> int:
    """Convert a RiskLevel string to an integer rank for escalation comparison."""
    return {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }.get(level, -1)


# =============================================================================
# RiskEngineService
# =============================================================================

class RiskEngineService:
    """
    Deterministic operational risk scoring engine.

    Transaction contract: callers are responsible for committing the session.
    This service flushes inside repository operations but never commits —
    preserving the UoW pattern used across the platform.

    This service MUST NOT:
      - Modify workflows, alert statuses, approvals, or any operational state.
      - Resolve alerts, acknowledge actions, or auto-transition any entity.
      - Make non-deterministic decisions (no randomness, no LLM calls).

    This service MAY:
      - Read any financial or operational table (read-only aggregation queries).
      - Insert new RiskAssessment records (append-only).
      - Append AuditLog entries for critical and escalating risk events.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = RiskAssessmentRepository()

    # -----------------------------------------------------------------------
    # Invoice risk scoring
    # -----------------------------------------------------------------------

    async def calculate_invoice_risk(
        self,
        *,
        organization_id: uuid.UUID,
        invoice_id: uuid.UUID,
    ) -> Optional[Tuple[int, str, Dict[str, Any], str, Dict[str, Any]]]:
        """
        Compute risk for a single invoice from operational signals.

        Returns (score, level, contributing_factors, explanation_text, source_snapshot)
        or None if the invoice does not exist.

        Signal sources (SQL-native aggregation only):
          - overdue_days:        days past due_date (0 if not yet due)
          - outstanding_amount:  total_amount − sum(RECEIVED payments)
          - unresolved_alerts:   OPEN/ACKNOWLEDGED alert count for this invoice
          - sla_breach_count:    alerts with sla_breached_at set
          - max_escalation:      highest escalation_level across active alerts
        """
        today = datetime.now(timezone.utc).date()

        paid_subq = (
            select(func.coalesce(func.sum(Payment.amount), Decimal("0.0000")))
            .where(
                Payment.invoice_id == invoice_id,
                Payment.status == PaymentStatus.RECEIVED,
                Payment.is_deleted.is_(False),
            )
            .scalar_subquery()
        )
        outstanding_expr = Invoice.total_amount - paid_subq

        inv_q = select(
            Invoice.id,
            Invoice.invoice_number,
            Invoice.total_amount,
            Invoice.due_date,
            Invoice.status,
            outstanding_expr.label("outstanding_amount"),
        ).where(
            Invoice.id == invoice_id,
            Invoice.organization_id == organization_id,
            Invoice.is_deleted.is_(False),
        )

        inv_row = (await self.db.execute(inv_q)).one_or_none()
        if inv_row is None:
            return None

        inv_id, inv_number, total_amount, due_date, inv_status, outstanding = inv_row
        outstanding = Decimal(str(outstanding))

        overdue_days = 0
        if due_date and due_date < today:
            overdue_days = (today - due_date).days

        alert_q = select(
            func.count(Alert.id).label("alert_count"),
            func.coalesce(
                func.sum(case((Alert.sla_breached_at.isnot(None), 1), else_=0)),
                0,
            ).label("sla_breach_count"),
            func.coalesce(func.max(Alert.escalation_level), 0).label("max_escalation"),
        ).where(
            Alert.organization_id == organization_id,
            Alert.entity_type == "invoice",
            Alert.entity_id == invoice_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        )

        alert_row = (await self.db.execute(alert_q)).one()
        alert_count      = int(alert_row.alert_count or 0)
        sla_breach_count = int(alert_row.sla_breach_count or 0)
        max_escalation   = int(alert_row.max_escalation or 0)

        # Factor scores (0–100 each)
        overdue_score     = _normalize(overdue_days, _INV_OVERDUE_DAYS_CEIL)
        outstanding_score = _normalize_decimal(outstanding, _INV_OUTSTANDING_CEIL)
        alert_score       = _normalize(alert_count, _INV_ALERT_CEIL)
        sla_score         = _normalize(sla_breach_count, _INV_SLA_BREACH_CEIL)
        escalation_score  = _normalize(max_escalation, _INV_ESCALATION_CEIL)

        weighted = (
            overdue_score     * _INV_W_OVERDUE_DAYS
            + outstanding_score * _INV_W_OUTSTANDING
            + alert_score       * _INV_W_ALERT_COUNT
            + sla_score         * _INV_W_SLA_BREACH
            + escalation_score  * _INV_W_ESCALATION
        )
        risk_score = _clamp_score(weighted)
        risk_level = _classify_risk(risk_score)

        contributing_factors: Dict[str, Any] = {
            "overdue_days":             overdue_days,
            "overdue_factor_score":     int(overdue_score),
            "overdue_weight":           str(_INV_W_OVERDUE_DAYS),
            "outstanding_amount":       str(outstanding),
            "outstanding_factor_score": int(outstanding_score),
            "outstanding_weight":       str(_INV_W_OUTSTANDING),
            "unresolved_alert_count":   alert_count,
            "alert_factor_score":       int(alert_score),
            "alert_weight":             str(_INV_W_ALERT_COUNT),
            "sla_breach_count":         sla_breach_count,
            "sla_breach_factor_score":  int(sla_score),
            "sla_breach_weight":        str(_INV_W_SLA_BREACH),
            "max_escalation_level":     max_escalation,
            "escalation_factor_score":  int(escalation_score),
            "escalation_weight":        str(_INV_W_ESCALATION),
        }

        reasons = []
        if overdue_days > 0:
            reasons.append(f"{overdue_days} overdue day{'s' if overdue_days != 1 else ''}")
        if outstanding > 0:
            reasons.append(f"₹{outstanding:,.0f} outstanding amount")
        if alert_count > 0:
            reasons.append(f"{alert_count} unresolved alert{'s' if alert_count != 1 else ''}")
        if sla_breach_count > 0:
            reasons.append("SLA breach recorded")
        if max_escalation > 0:
            reasons.append(f"escalated to level {max_escalation}")

        if reasons:
            explanation_text = (
                f"Invoice {inv_number} is {risk_level} risk due to: "
                + "; ".join(reasons) + "."
            )
        else:
            explanation_text = (
                f"Invoice {inv_number} is {risk_level} risk with no critical signals."
            )

        source_snapshot: Dict[str, Any] = {
            "invoice_number":     inv_number,
            "invoice_status":     inv_status,
            "total_amount":       str(total_amount),
            "outstanding_amount": str(outstanding),
            "due_date":           str(due_date) if due_date else None,
            "overdue_days":       overdue_days,
            "assessed_at":        datetime.now(timezone.utc).isoformat(),
        }

        return (risk_score, risk_level, contributing_factors, explanation_text, source_snapshot)

    # -----------------------------------------------------------------------
    # Vendor risk scoring
    # -----------------------------------------------------------------------

    async def calculate_vendor_risk(
        self,
        *,
        organization_id: uuid.UUID,
        vendor_id: uuid.UUID,
    ) -> Optional[Tuple[int, str, Dict[str, Any], str, Dict[str, Any]]]:
        """
        Compute operational risk for a vendor from cross-entity signals.

        Signal sources (SQL-native aggregation only):
          - overdue_invoice_ratio:    overdue invoices / total active invoices
          - unresolved_liabilities:   RECEIVED payments with pending settlement amount
          - delayed_settlement_count: unsettled payments older than threshold days
          - sla_breach_count:         invoice-level alerts with sla_breached_at set
        """
        vendor_q = select(
            Vendor.id, Vendor.legal_name, Vendor.vendor_code,
        ).where(
            Vendor.id == vendor_id,
            Vendor.organization_id == organization_id,
            Vendor.is_deleted.is_(False),
        )
        vendor_row = (await self.db.execute(vendor_q)).one_or_none()
        if vendor_row is None:
            return None

        _v_id, legal_name, vendor_code = vendor_row
        today = datetime.now(timezone.utc).date()

        # Total active invoices for this vendor
        total_inv_q = select(func.count(Invoice.id)).where(
            Invoice.organization_id == organization_id,
            Invoice.vendor_id == vendor_id,
            Invoice.is_deleted.is_(False),
            Invoice.status.notin_([InvoiceStatus.CANCELLED, InvoiceStatus.PAID]),
        )
        total_inv = int((await self.db.execute(total_inv_q)).scalar_one() or 0)

        # Overdue invoices for this vendor
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

        overdue_inv_q = select(func.count(Invoice.id)).where(
            Invoice.organization_id == organization_id,
            Invoice.vendor_id == vendor_id,
            Invoice.is_deleted.is_(False),
            Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.ISSUED]),
            Invoice.due_date < today,
            outstanding_expr > Decimal("0"),
        )
        overdue_inv = int((await self.db.execute(overdue_inv_q)).scalar_one() or 0)

        overdue_ratio = (
            Decimal(str(overdue_inv)) / Decimal(str(total_inv))
            if total_inv > 0 else Decimal("0")
        )

        # Unresolved liabilities: RECEIVED payments with unsettled balance
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

        unresolved_q = (
            select(func.count(Payment.id))
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .where(
                Payment.organization_id == organization_id,
                Payment.status == PaymentStatus.RECEIVED,
                Payment.is_deleted.is_(False),
                unsettled_expr > Decimal("0"),
                Invoice.vendor_id == vendor_id,
                Invoice.is_deleted.is_(False),
            )
        )
        unresolved_liab = int((await self.db.execute(unresolved_q)).scalar_one() or 0)

        # Delayed settlements: unsettled AND older than threshold
        cutoff_7days = datetime.now(timezone.utc) - timedelta(days=_DELAYED_SETTLEMENT_DAYS)
        delayed_q = (
            select(func.count(Payment.id))
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .where(
                Payment.organization_id == organization_id,
                Payment.status == PaymentStatus.RECEIVED,
                Payment.is_deleted.is_(False),
                Payment.payment_date < cutoff_7days,
                unsettled_expr > Decimal("0"),
                Invoice.vendor_id == vendor_id,
                Invoice.is_deleted.is_(False),
            )
        )
        delayed_count = int((await self.db.execute(delayed_q)).scalar_one() or 0)

        # SLA breaches on invoice-level alerts for this vendor
        sla_breach_q = (
            select(func.count(Alert.id))
            .join(Invoice, and_(
                Alert.entity_id == Invoice.id,
                Alert.entity_type == "invoice",
            ))
            .where(
                Alert.organization_id == organization_id,
                Invoice.vendor_id == vendor_id,
                Invoice.is_deleted.is_(False),
                Alert.sla_breached_at.isnot(None),
            )
        )
        sla_breach_count = int((await self.db.execute(sla_breach_q)).scalar_one() or 0)

        # Factor scores (0–100 each)
        overdue_ratio_score = Decimal(str(min(100, int(overdue_ratio * 100))))
        unresolved_score    = _normalize(unresolved_liab, _VEN_UNRESOLVED_LIAB_CEIL)
        delayed_score       = _normalize(delayed_count, _VEN_DELAYED_SETTLEM_CEIL)
        sla_score           = _normalize(sla_breach_count, _VEN_SLA_BREACH_CEIL)

        weighted = (
            overdue_ratio_score * _VEN_W_OVERDUE_RATIO
            + unresolved_score  * _VEN_W_UNRESOLVED_LIAB
            + delayed_score     * _VEN_W_DELAYED_SETTLEM
            + sla_score         * _VEN_W_SLA_BREACH
        )
        risk_score = _clamp_score(weighted)
        risk_level = _classify_risk(risk_score)

        contributing_factors: Dict[str, Any] = {
            "total_active_invoices":       total_inv,
            "overdue_invoice_count":       overdue_inv,
            "overdue_invoice_ratio":       str(overdue_ratio.quantize(Decimal("0.0001"))),
            "overdue_ratio_factor_score":  int(overdue_ratio_score),
            "overdue_ratio_weight":        str(_VEN_W_OVERDUE_RATIO),
            "unresolved_liabilities":      unresolved_liab,
            "unresolved_factor_score":     int(unresolved_score),
            "unresolved_weight":           str(_VEN_W_UNRESOLVED_LIAB),
            "delayed_settlement_count":    delayed_count,
            "delayed_factor_score":        int(delayed_score),
            "delayed_weight":              str(_VEN_W_DELAYED_SETTLEM),
            "sla_breach_count":            sla_breach_count,
            "sla_breach_factor_score":     int(sla_score),
            "sla_breach_weight":           str(_VEN_W_SLA_BREACH),
        }

        reasons = []
        if overdue_inv > 0:
            pct = int(overdue_ratio * 100)
            reasons.append(
                f"{overdue_inv} overdue invoice{'s' if overdue_inv != 1 else ''} ({pct}% of total)"
            )
        if unresolved_liab > 0:
            reasons.append(
                f"{unresolved_liab} unresolved liabilit{'ies' if unresolved_liab != 1 else 'y'}"
            )
        if delayed_count > 0:
            reasons.append(
                f"{delayed_count} delayed settlement{'s' if delayed_count != 1 else ''}"
            )
        if sla_breach_count > 0:
            reasons.append(
                f"{sla_breach_count} SLA breach{'es' if sla_breach_count != 1 else ''}"
            )

        vendor_label = legal_name or str(vendor_id)[:8]
        if reasons:
            explanation_text = (
                f"Vendor {vendor_label} is {risk_level} risk due to: "
                + "; ".join(reasons) + "."
            )
        else:
            explanation_text = (
                f"Vendor {vendor_label} is {risk_level} risk with no critical signals."
            )

        source_snapshot: Dict[str, Any] = {
            "vendor_name":         legal_name,
            "vendor_code":         vendor_code,
            "total_invoices":      total_inv,
            "overdue_invoices":    overdue_inv,
            "unresolved_liab":     unresolved_liab,
            "delayed_settlements": delayed_count,
            "sla_breaches":        sla_breach_count,
            "assessed_at":         datetime.now(timezone.utc).isoformat(),
        }

        return (risk_score, risk_level, contributing_factors, explanation_text, source_snapshot)

    # -----------------------------------------------------------------------
    # Settlement (payment) risk scoring
    # -----------------------------------------------------------------------

    async def calculate_settlement_risk(
        self,
        *,
        organization_id: uuid.UUID,
        payment_id: uuid.UUID,
    ) -> Optional[Tuple[int, str, Dict[str, Any], str, Dict[str, Any]]]:
        """
        Compute settlement risk for a RECEIVED payment.

        entity_type = "payment" (settlement risk is assessed at the payment level,
        consistent with the alert scanner's entity_type for unsettled liabilities).

        Signal sources (SQL-native aggregation only):
          - settlement_aging_days:    days since payment was received
          - pending_amount:           payment.amount − sum(SETTLED vendor_settlements)
          - partial_settlement_count: number of vendor_settlement records for payment
          - unresolved_alert_count:   OPEN/ACKNOWLEDGED alerts on this payment
        """
        settled_subq = (
            select(func.coalesce(func.sum(VendorSettlement.amount), Decimal("0.0000")))
            .where(
                VendorSettlement.payment_id == payment_id,
                VendorSettlement.status == SettlementStatus.SETTLED,
                VendorSettlement.is_deleted.is_(False),
            )
            .scalar_subquery()
        )
        partial_count_subq = (
            select(func.count(VendorSettlement.id))
            .where(
                VendorSettlement.payment_id == payment_id,
                VendorSettlement.is_deleted.is_(False),
            )
            .scalar_subquery()
        )
        pending_expr = Payment.amount - settled_subq

        pay_q = select(
            Payment.id,
            Payment.payment_reference,
            Payment.amount,
            Payment.payment_date,
            Payment.status,
            pending_expr.label("pending_amount"),
            partial_count_subq.label("partial_count"),
        ).where(
            Payment.id == payment_id,
            Payment.organization_id == organization_id,
            Payment.is_deleted.is_(False),
        )

        pay_row = (await self.db.execute(pay_q)).one_or_none()
        if pay_row is None:
            return None

        pay_id, pay_ref, pay_amount, pay_date, pay_status, pending_amount, partial_count = pay_row
        pending_amount = Decimal(str(pending_amount))

        now_utc = datetime.now(timezone.utc)
        aging_days = 0
        if pay_date:
            if getattr(pay_date, "tzinfo", None):
                aging_days = max(0, (now_utc - pay_date).days)
            else:
                aging_days = max(0, (now_utc.replace(tzinfo=None) - pay_date).days)

        alert_q = select(func.count(Alert.id)).where(
            Alert.organization_id == organization_id,
            Alert.entity_type == "payment",
            Alert.entity_id == payment_id,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        )
        alert_count = int((await self.db.execute(alert_q)).scalar_one() or 0)

        # Factor scores (0–100 each)
        aging_score   = _normalize(aging_days, _SET_AGING_CEIL)
        pending_score = _normalize_decimal(pending_amount, _SET_PENDING_CEIL)
        partial_score = _normalize(int(partial_count or 0), _SET_PARTIAL_CEIL)
        alert_score   = _normalize(alert_count, _SET_ALERTS_CEIL)

        weighted = (
            aging_score   * _SET_W_AGING_DAYS
            + pending_score * _SET_W_PENDING_AMT
            + partial_score * _SET_W_PARTIAL_COUNT
            + alert_score   * _SET_W_ALERTS
        )
        risk_score = _clamp_score(weighted)
        risk_level = _classify_risk(risk_score)

        contributing_factors: Dict[str, Any] = {
            "settlement_aging_days":      aging_days,
            "aging_factor_score":         int(aging_score),
            "aging_weight":               str(_SET_W_AGING_DAYS),
            "pending_amount":             str(pending_amount),
            "pending_factor_score":       int(pending_score),
            "pending_weight":             str(_SET_W_PENDING_AMT),
            "partial_settlement_count":   int(partial_count or 0),
            "partial_factor_score":       int(partial_score),
            "partial_weight":             str(_SET_W_PARTIAL_COUNT),
            "unresolved_alert_count":     alert_count,
            "alert_factor_score":         int(alert_score),
            "alert_weight":               str(_SET_W_ALERTS),
        }

        reasons = []
        if aging_days > 0:
            reasons.append(f"{aging_days}-day-old payment pending settlement")
        if pending_amount > 0:
            reasons.append(f"₹{pending_amount:,.0f} pending")
        if int(partial_count or 0) > 1:
            reasons.append(f"{partial_count} partial settlement records")
        if alert_count > 0:
            reasons.append(f"{alert_count} unresolved alert{'s' if alert_count != 1 else ''}")

        if reasons:
            explanation_text = (
                f"Settlement for payment {pay_ref} is {risk_level} risk due to: "
                + "; ".join(reasons) + "."
            )
        else:
            explanation_text = (
                f"Settlement for payment {pay_ref} is {risk_level} risk with no critical signals."
            )

        source_snapshot: Dict[str, Any] = {
            "payment_reference":        pay_ref,
            "payment_amount":           str(pay_amount),
            "pending_amount":           str(pending_amount),
            "payment_status":           pay_status,
            "aging_days":               aging_days,
            "partial_settlement_count": int(partial_count or 0),
            "assessed_at":              now_utc.isoformat(),
        }

        return (risk_score, risk_level, contributing_factors, explanation_text, source_snapshot)

    # -----------------------------------------------------------------------
    # Orchestration: calculate + persist a risk assessment
    # -----------------------------------------------------------------------

    async def generate_risk_assessment(
        self,
        *,
        organization_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        dedup_minutes: int = 0,
    ) -> Optional[RiskAssessment]:
        """
        Calculate and persist a risk assessment for the given entity.

        Dedup gate: if dedup_minutes > 0 and a recent assessment was created
        within that window, returns None — prevents scanner spam without losing
        historical trend data.

        Fetches the previous risk level internally to detect escalation
        transitions without requiring the caller to supply it.

        Audit strategy (signal-rich events only — avoids low-noise audit spam):
          CRITICAL              → RISK_CRITICAL_CLASSIFIED
          level increased       → RISK_LEVEL_ESCALATED
          HIGH (no transition)  → RISK_ASSESSMENT_GENERATED
          LOW / MEDIUM          → no audit entry

        Returns the persisted RiskAssessment, or None if entity not found / deduped.
        """
        # Dedup check
        if dedup_minutes > 0:
            recent = await self._repo.find_recent(
                self.db,
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
                within_minutes=dedup_minutes,
            )
            if recent is not None:
                logger.debug(
                    "Risk dedup: skip %s/%s (assessed < %dm ago)",
                    entity_type, entity_id, dedup_minutes,
                )
                return None

        # Determine previous risk level for escalation audit detection
        previous_level: Optional[str] = None
        latest = await self._repo.get_latest_for_entity(
            self.db,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if latest is not None:
            previous_level = latest.risk_level

        # Delegate to entity-specific calculator
        result: Optional[Tuple] = None
        if entity_type == RiskEntityType.INVOICE:
            result = await self.calculate_invoice_risk(
                organization_id=organization_id, invoice_id=entity_id,
            )
        elif entity_type == RiskEntityType.VENDOR:
            result = await self.calculate_vendor_risk(
                organization_id=organization_id, vendor_id=entity_id,
            )
        elif entity_type == RiskEntityType.PAYMENT:
            result = await self.calculate_settlement_risk(
                organization_id=organization_id, payment_id=entity_id,
            )
        else:
            logger.warning("Unknown entity_type for risk assessment: %s", entity_type)
            return None

        if result is None:
            return None

        score, level, factors, explanation, snapshot = result

        assessment = await self._repo.create(
            self.db,
            obj_in={
                "organization_id":      organization_id,
                "entity_type":          entity_type,
                "entity_id":            entity_id,
                "risk_score":           score,
                "risk_level":           level,
                "contributing_factors": factors,
                "explanation_text":     explanation,
                "generated_at":         datetime.now(timezone.utc),
                "source_snapshot_json": snapshot,
            },
        )

        await self._audit_assessment(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            score=score,
            level=level,
            previous_level=previous_level,
            assessment_id=assessment.id,
        )

        return assessment

    # -----------------------------------------------------------------------
    # Internal: selective audit logging
    # -----------------------------------------------------------------------

    async def _audit_assessment(
        self,
        *,
        organization_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        score: int,
        level: str,
        previous_level: Optional[str],
        assessment_id: uuid.UUID,
    ) -> None:
        meta = {
            "risk_score":    score,
            "risk_level":    level,
            "assessment_id": str(assessment_id),
        }

        if level == RiskLevel.CRITICAL:
            await AuditService.log_event(
                self.db,
                entity_type=entity_type,
                entity_id=entity_id,
                action=AuditAction.RISK_CRITICAL_CLASSIFIED,
                metadata=meta,
            )
        elif (
            previous_level is not None
            and _level_to_int(level) > _level_to_int(previous_level)
        ):
            await AuditService.log_event(
                self.db,
                entity_type=entity_type,
                entity_id=entity_id,
                action=AuditAction.RISK_LEVEL_ESCALATED,
                field_name="risk_level",
                old_value=previous_level,
                new_value=level,
                metadata=meta,
            )
        elif level == RiskLevel.HIGH:
            await AuditService.log_event(
                self.db,
                entity_type=entity_type,
                entity_id=entity_id,
                action=AuditAction.RISK_ASSESSMENT_GENERATED,
                metadata=meta,
            )
        # LOW / MEDIUM → no audit entry (avoids filling log with low-signal events)
