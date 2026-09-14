"""d_ai_modules: captures, daily_briefings, weekly_reviews

Revision ID: d1000000ai
Revises: a1000000local
Create Date: 2026-09-14

Stream D's single migration. down_revision is stream A's head as instructed; stream E writes the merge migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'd1000000ai'
down_revision = 'a1000000local'
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
        'captures',
        *_base_columns(),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('parsed_type', sa.String(length=20), nullable=True),
        sa.Column('parsed_json', JSON, nullable=True),
        sa.Column('result_ref', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_captures_status', 'captures', ['status'])

    op.create_table(
        'daily_briefings',
        *_base_columns(),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('context_json', JSON, nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_daily_briefings_date'),
    )

    op.create_table(
        'weekly_reviews',
        *_base_columns(),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('stats_json', JSON, nullable=True),
        sa.Column('reflection', sa.Text(), nullable=True),
        sa.Column('reflection_source', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('next_week_focus', JSON, nullable=True),
        sa.Column('finalized', sa.Boolean(), nullable=False),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_start', name='uq_weekly_reviews_week_start'),
    )


def downgrade():
    op.drop_table('weekly_reviews')
    op.drop_table('daily_briefings')
    op.drop_table('captures')
