"""add alert table with partial unique dedup index

Revision ID: c7f3a9b21e04
Revises: 5a82a9dbcef4
Create Date: 2026-05-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c7f3a9b21e04'
down_revision = '5a82a9dbcef4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alert',
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.UUID(), nullable=True),
        sa.Column('resolved_by_user_id', sa.UUID(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['acknowledged_by_user_id'], ['user.id'],
            name=op.f('fk_alert_acknowledged_by_user_id_user'),
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organization.id'],
            name=op.f('fk_alert_organization_id_organization'),
            ondelete='RESTRICT',
        ),
        sa.ForeignKeyConstraint(
            ['resolved_by_user_id'], ['user.id'],
            name=op.f('fk_alert_resolved_by_user_id_user'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_alert')),
    )

    # Regular read/lookup indexes
    op.create_index(op.f('ix_alert_alert_type'), 'alert', ['alert_type'], unique=False)
    op.create_index(op.f('ix_alert_entity_id'), 'alert', ['entity_id'], unique=False)
    op.create_index(op.f('ix_alert_entity_type'), 'alert', ['entity_type'], unique=False)
    op.create_index(op.f('ix_alert_organization_id'), 'alert', ['organization_id'], unique=False)
    op.create_index(op.f('ix_alert_severity'), 'alert', ['severity'], unique=False)
    op.create_index(op.f('ix_alert_status'), 'alert', ['status'], unique=False)
    op.create_index(op.f('ix_alert_triggered_at'), 'alert', ['triggered_at'], unique=False)

    # Composite read index for filtered list queries
    op.create_index(
        'ix_alert_tenant_type_entity',
        'alert',
        ['organization_id', 'alert_type', 'entity_type', 'entity_id'],
        unique=False,
    )
    # Status + recency ordered list index
    op.create_index(
        'ix_alert_status_triggered',
        'alert',
        ['status', 'triggered_at'],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # CRITICAL: Partial unique index for DB-level concurrency-safe deduplication.
    #
    # Guarantees at most one OPEN or ACKNOWLEDGED alert per
    # (organization_id, alert_type, entity_type, entity_id) combination.
    #
    # The WHERE clause excludes RESOLVED alerts so a re-appearing issue
    # (after the previous alert was resolved) can generate a new alert.
    #
    # This is the database-level backstop against concurrent scheduler runs
    # that both pass the application-level find_active() check simultaneously.
    # -------------------------------------------------------------------------
    op.create_index(
        'uq_alert_active_dedup',
        'alert',
        ['organization_id', 'alert_type', 'entity_type', 'entity_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('OPEN', 'ACKNOWLEDGED')"),
    )


def downgrade() -> None:
    op.drop_index('uq_alert_active_dedup', table_name='alert')
    op.drop_index('ix_alert_status_triggered', table_name='alert')
    op.drop_index('ix_alert_tenant_type_entity', table_name='alert')
    op.drop_index(op.f('ix_alert_triggered_at'), table_name='alert')
    op.drop_index(op.f('ix_alert_status'), table_name='alert')
    op.drop_index(op.f('ix_alert_severity'), table_name='alert')
    op.drop_index(op.f('ix_alert_organization_id'), table_name='alert')
    op.drop_index(op.f('ix_alert_entity_type'), table_name='alert')
    op.drop_index(op.f('ix_alert_entity_id'), table_name='alert')
    op.drop_index(op.f('ix_alert_alert_type'), table_name='alert')
    op.drop_table('alert')
