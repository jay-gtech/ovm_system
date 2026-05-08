"""add SLA policies, notifications, and alert escalation fields

Revision ID: e2d4f6a8b0c1
Revises: c7f3a9b21e04
Create Date: 2026-05-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e2d4f6a8b0c1'
down_revision = 'c7f3a9b21e04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Alert table — add escalation tracking columns
    # -------------------------------------------------------------------------
    op.add_column('alert', sa.Column(
        'escalation_level', sa.Integer(), nullable=False, server_default='0'
    ))
    op.add_column('alert', sa.Column(
        'escalated_at', sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column('alert', sa.Column(
        'sla_breached_at', sa.DateTime(timezone=True), nullable=True
    ))
    op.create_index(
        op.f('ix_alert_escalation_level'), 'alert', ['escalation_level'], unique=False
    )
    op.create_index(
        op.f('ix_alert_sla_breached_at'), 'alert', ['sla_breached_at'], unique=False
    )

    # -------------------------------------------------------------------------
    # 2. sla_policy table
    # -------------------------------------------------------------------------
    op.create_table(
        'sla_policy',
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('acknowledgement_minutes', sa.Integer(), nullable=False),
        sa.Column('resolution_minutes', sa.Integer(), nullable=False),
        sa.Column('escalation_level_1_minutes', sa.Integer(), nullable=False),
        sa.Column('escalation_level_2_minutes', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organization.id'],
            name=op.f('fk_sla_policy_organization_id_organization'),
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sla_policy')),
        sa.UniqueConstraint(
            'organization_id', 'alert_type',
            name='uq_sla_policy_org_alert_type',
        ),
    )
    op.create_index(
        op.f('ix_sla_policy_alert_type'), 'sla_policy', ['alert_type'], unique=False
    )
    op.create_index(
        op.f('ix_sla_policy_organization_id'), 'sla_policy', ['organization_id'],
        unique=False
    )

    # -------------------------------------------------------------------------
    # 3. notification table
    # -------------------------------------------------------------------------
    op.create_table(
        'notification',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.UUID(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organization.id'],
            name=op.f('fk_notification_organization_id_organization'),
            ondelete='RESTRICT',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['user.id'],
            name=op.f('fk_notification_user_id_user'),
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_notification')),
    )
    op.create_index(
        op.f('ix_notification_notification_type'), 'notification',
        ['notification_type'], unique=False
    )
    op.create_index(
        op.f('ix_notification_organization_id'), 'notification',
        ['organization_id'], unique=False
    )
    op.create_index(
        op.f('ix_notification_status'), 'notification', ['status'], unique=False
    )
    op.create_index(
        op.f('ix_notification_user_id'), 'notification', ['user_id'], unique=False
    )
    # Composite indexes declared in the model
    op.create_index(
        'ix_notification_user_status', 'notification', ['user_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_notification_org_entity', 'notification',
        ['organization_id', 'notification_type', 'related_entity_id'],
        unique=False
    )


def downgrade() -> None:
    # notification
    op.drop_index('ix_notification_org_entity', table_name='notification')
    op.drop_index('ix_notification_user_status', table_name='notification')
    op.drop_index(op.f('ix_notification_user_id'), table_name='notification')
    op.drop_index(op.f('ix_notification_status'), table_name='notification')
    op.drop_index(op.f('ix_notification_organization_id'), table_name='notification')
    op.drop_index(op.f('ix_notification_notification_type'), table_name='notification')
    op.drop_table('notification')

    # sla_policy
    op.drop_index(op.f('ix_sla_policy_organization_id'), table_name='sla_policy')
    op.drop_index(op.f('ix_sla_policy_alert_type'), table_name='sla_policy')
    op.drop_table('sla_policy')

    # alert escalation columns
    op.drop_index(op.f('ix_alert_sla_breached_at'), table_name='alert')
    op.drop_index(op.f('ix_alert_escalation_level'), table_name='alert')
    op.drop_column('alert', 'sla_breached_at')
    op.drop_column('alert', 'escalated_at')
    op.drop_column('alert', 'escalation_level')
