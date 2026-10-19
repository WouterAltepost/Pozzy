"""j_habits: schedules, skips, icons and reminders for habits; Web Push subscriptions

Revision ID: j1000000habits
Revises: i1000000rls
Create Date: 2026-10-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'j1000000habits'
down_revision = 'i1000000rls'
branch_labels = None
depends_on = None


def upgrade():
    # Existing habits keep their behaviour: due every day.
    op.add_column('trackers', sa.Column('schedule', sa.String(length=20), nullable=False, server_default='daily'))
    op.add_column('trackers', sa.Column('schedule_days', sa.Integer(), nullable=True))
    op.add_column('trackers', sa.Column('schedule_n', sa.Integer(), nullable=True))
    op.add_column('trackers', sa.Column('icon', sa.String(length=40), nullable=True))
    op.add_column('trackers', sa.Column('reminder_time', sa.String(length=5), nullable=True))
    op.add_column('trackers', sa.Column('last_reminded_on', sa.Date(), nullable=True))
    op.add_column('tracker_entries', sa.Column('status', sa.String(length=10), nullable=False, server_default='done'))
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.String(length=200), nullable=False),
        sa.Column('auth', sa.String(length=100), nullable=False),
        sa.Column('user_agent', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint', name='uq_push_subscriptions_endpoint'),
    )
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_table('push_subscriptions')
    op.drop_column('tracker_entries', 'status')
    for col in ('last_reminded_on', 'reminder_time', 'icon', 'schedule_n', 'schedule_days', 'schedule'):
        op.drop_column('trackers', col)
