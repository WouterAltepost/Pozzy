"""h_hours_suggestions: hours logs remember what they were logged from; dismissed suggestions

Revision ID: h1000000hours
Revises: g1000000notes
Create Date: 2026-09-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'h1000000hours'
down_revision = 'g1000000notes'
branch_labels = None
depends_on = None


def upgrade():
    # "event:<uid>|<recurrence_id>" or "task:<id>": the agenda event or completed task a log was
    # made from, so the same source is never suggested twice.
    op.add_column('hours_logs', sa.Column('source_ref', sa.String(length=400), nullable=True))
    op.create_index('ix_hours_logs_source_ref', 'hours_logs', ['source_ref'])
    op.create_table(
        'hours_dismissals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('ref', sa.String(length=400), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ref', name='uq_hours_dismissals_ref'),
    )


def downgrade():
    op.drop_table('hours_dismissals')
    op.drop_index('ix_hours_logs_source_ref', table_name='hours_logs')
    op.drop_column('hours_logs', 'source_ref')
