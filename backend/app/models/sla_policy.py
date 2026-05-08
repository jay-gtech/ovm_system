from sqlalchemy import String, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import TenantBaseModel


class SLAPolicy(TenantBaseModel):
    """
    Per-tenant, per-alert-type SLA timing configuration.

    Design rules:
    - No soft-delete: policies are operational config, not financial records.
    - Uniqueness: one active policy per (organization_id, alert_type).
    - Minutes-based: all windows stored as integer minutes for arithmetic simplicity.

    SLA clock reference: alert.triggered_at.

    Escalation flow enforced by SLAService (no downgrade):
        Level 0 (new) → Level 1 (acknowledgement_minutes breached while OPEN)
        Level 1       → Level 2 (escalation_level_2_minutes elapsed, still active)
        Any level     → sla_breached_at stamped once resolution_minutes elapsed
    """

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "alert_type",
            name="uq_sla_policy_org_alert_type",
        ),
    )

    alert_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # How many minutes the alert must be OPEN before acknowledgement is overdue.
    acknowledgement_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    # Total minutes from triggered_at before the alert is considered SLA-breached.
    resolution_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=480
    )
    # Minutes from triggered_at that trigger escalation to level 1.
    escalation_level_1_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=120
    )
    # Minutes from triggered_at that trigger escalation to level 2.
    escalation_level_2_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=360
    )

    def __repr__(self) -> str:
        return (
            f"<SLAPolicy(alert_type={self.alert_type}, active={self.is_active}, "
            f"ack={self.acknowledgement_minutes}m, res={self.resolution_minutes}m)>"
        )
