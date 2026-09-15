"""g_briefing_notes: notes_json on daily_briefings (briefing replies with proposed actions)

Revision ID: g1000000notes
Revises: e1000000merge
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g1000000notes'
down_revision = 'e1000000merge'
branch_labels = None
depends_on = None

JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def upgrade():
    op.add_column('daily_briefings', sa.Column('notes_json', JSON, nullable=True))


def downgrade():
    op.drop_column('daily_briefings', 'notes_json')
