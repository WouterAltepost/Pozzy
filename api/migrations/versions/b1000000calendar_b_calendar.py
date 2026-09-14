"""b_calendar: calendar_accounts, calendar_events

Revision ID: b1000000calendar
Revises: 722da3773e5d
Create Date: 2026-09-14

Stream B's single migration. down_revision is the M1 head; stream E writes the merge migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b1000000calendar'
down_revision = '722da3773e5d'
branch_labels = None
depends_on = None

JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def _base_columns():
    return [
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    ]


def upgrade():
    op.create_table(
        'calendar_accounts',
        *_base_columns(),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('caldav_url', sa.String(length=500), nullable=False),
        sa.Column('username', sa.String(length=200), nullable=False),
        sa.Column('secret_ref', sa.String(length=100), nullable=False),
        sa.Column('calendar_urls', JSON, nullable=False),
        sa.Column('write_calendar_url', sa.String(length=500), nullable=True),
        sa.Column('known_calendars', JSON, nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'calendar_events',
        *_base_columns(),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('calendar_url', sa.String(length=500), nullable=False),
        sa.Column('uid', sa.String(length=255), nullable=False),
        sa.Column('recurrence_id', sa.String(length=64), nullable=False),
        sa.Column('etag', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), nullable=False),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['calendar_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('calendar_url', 'uid', 'recurrence_id', name='uq_calendar_events_occurrence'),
    )
    op.create_index('ix_calendar_events_account_id', 'calendar_events', ['account_id'])
    op.create_index('ix_calendar_events_calendar_url', 'calendar_events', ['calendar_url'])
    op.create_index('ix_calendar_events_uid', 'calendar_events', ['uid'])
    op.create_index('ix_calendar_events_start', 'calendar_events', ['start'])
    op.create_index('ix_calendar_events_end', 'calendar_events', ['end'])
    op.create_index('ix_calendar_events_task_id', 'calendar_events', ['task_id'])


def downgrade():
    op.drop_table('calendar_events')
    op.drop_table('calendar_accounts')
