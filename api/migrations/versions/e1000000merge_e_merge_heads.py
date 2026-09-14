"""e_merge_heads: merge stream B, C and D migrations into one head

Revision ID: e1000000merge
Revises: b1000000calendar, c1000000mail, d1000000ai
Create Date: 2026-09-14

Stream E. No schema changes, only joins the three parallel heads.
"""

revision = 'e1000000merge'
down_revision = ('b1000000calendar', 'c1000000mail', 'd1000000ai')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
