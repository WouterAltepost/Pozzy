"""a_local_modules: tasks, daily_dos, weekly_goals, trackers, tracker_entries, hours_logs, notes, courses, deadlines, applications

Revision ID: a1000000local
Revises: 722da3773e5d
Create Date: 2026-09-14

Stream A's single migration. down_revision is the M1 head; stream E writes the merge migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1000000local'
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
        'tasks',
        *_base_columns(),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('tags', JSON, nullable=False),
        sa.Column('urgent', sa.Boolean(), nullable=False),
        sa.Column('important', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_uid', sa.String(length=255), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('source_ref', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_area_id', 'tasks', ['area_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('ix_tasks_calendar_uid', 'tasks', ['calendar_uid'])

    op.create_table(
        'hours_logs',
        *_base_columns(),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('tags', JSON, nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hours_logs_date', 'hours_logs', ['date'])
    op.create_index('ix_hours_logs_area_id', 'hours_logs', ['area_id'])
    op.create_index('ix_hours_logs_task_id', 'hours_logs', ['task_id'])


def downgrade():
    op.drop_table('hours_logs')
    op.drop_table('tasks')
