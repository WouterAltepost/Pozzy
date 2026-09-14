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

    op.create_table(
        'daily_dos',
        *_base_columns(),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('done', sa.Boolean(), nullable=False),
        sa.Column('rolled_from_date', sa.Date(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_daily_dos_date', 'daily_dos', ['date'])
    op.create_index('ix_daily_dos_task_id', 'daily_dos', ['task_id'])

    op.create_table(
        'weekly_goals',
        *_base_columns(),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('done', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_weekly_goals_week_start', 'weekly_goals', ['week_start'])
    op.create_index('ix_weekly_goals_area_id', 'weekly_goals', ['area_id'])

    op.create_table(
        'trackers',
        *_base_columns(),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('target_period', sa.String(length=10), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trackers_area_id', 'trackers', ['area_id'])

    op.create_table(
        'tracker_entries',
        *_base_columns(),
        sa.Column('tracker_id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id', 'date', name='uq_tracker_entries_tracker_date'),
    )
    op.create_index('ix_tracker_entries_tracker_id', 'tracker_entries', ['tracker_id'])
    op.create_index('ix_tracker_entries_date', 'tracker_entries', ['date'])

    op.create_table(
        'notes',
        *_base_columns(),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('tags', JSON, nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notes_area_id', 'notes', ['area_id'])

    op.create_table(
        'courses',
        *_base_columns(),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('period', sa.String(length=50), nullable=True),
        sa.Column('ects', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'deadlines',
        *_base_columns(),
        sa.Column('course_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('done', sa.Boolean(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deadlines_course_id', 'deadlines', ['course_id'])
    op.create_index('ix_deadlines_due_at', 'deadlines', ['due_at'])
    op.create_index('ix_deadlines_task_id', 'deadlines', ['task_id'])

    op.create_table(
        'applications',
        *_base_columns(),
        sa.Column('company', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('applied_at', sa.Date(), nullable=True),
        sa.Column('next_step', sa.String(length=200), nullable=True),
        sa.Column('next_step_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_status', 'applications', ['status'])
    op.create_index('ix_applications_next_step_date', 'applications', ['next_step_date'])


def downgrade():
    op.drop_table('applications')
    op.drop_table('deadlines')
    op.drop_table('courses')
    op.drop_table('notes')
    op.drop_table('tracker_entries')
    op.drop_table('trackers')
    op.drop_table('weekly_goals')
    op.drop_table('daily_dos')
    op.drop_table('hours_logs')
    op.drop_table('tasks')
