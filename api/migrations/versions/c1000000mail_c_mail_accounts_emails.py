"""c_mail_accounts_emails: mail_accounts, emails

Revision ID: c1000000mail
Revises: a1000000local
Create Date: 2026-09-14

Stream C's single migration. down_revision is stream A's head (on main); stream E writes the merge migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c1000000mail'
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
        'mail_accounts',
        *_base_columns(),
        sa.Column('label', sa.String(length=60), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('imap_host', sa.String(length=255), nullable=False),
        sa.Column('secret_ref', sa.String(length=255), nullable=True),
        sa.Column('last_uid', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_mail_accounts_email'),
    )

    op.create_table(
        'emails',
        *_base_columns(),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('uid', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=998), nullable=True),
        sa.Column('thread_hint', sa.String(length=998), nullable=True),
        sa.Column('from_name', sa.String(length=255), nullable=False),
        sa.Column('from_email', sa.String(length=320), nullable=False),
        sa.Column('to_addrs', JSON, nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=False),
        sa.Column('labels', JSON, nullable=False),
        sa.Column('has_attachments', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=30), nullable=True),
        sa.Column('area_id', sa.Uuid(), nullable=True),
        sa.Column('needs_reply', sa.Boolean(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('classifier', sa.String(length=20), nullable=True),
        sa.Column('classified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority_override', sa.Integer(), nullable=True),
        sa.Column('category_override', sa.String(length=30), nullable=True),
        sa.Column('area_override_id', sa.Uuid(), nullable=True),
        sa.Column('handled', sa.Boolean(), nullable=False),
        sa.Column('handled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['mail_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.ForeignKeyConstraint(['area_override_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'uid', name='uq_emails_account_uid'),
    )
    op.create_index('ix_emails_account_id', 'emails', ['account_id'])
    op.create_index('ix_emails_message_id', 'emails', ['message_id'])
    op.create_index('ix_emails_from_email', 'emails', ['from_email'])
    op.create_index('ix_emails_date', 'emails', ['date'])
    op.create_index('ix_emails_priority', 'emails', ['priority'])
    op.create_index('ix_emails_classified_at', 'emails', ['classified_at'])
    op.create_index('ix_emails_handled', 'emails', ['handled'])


def downgrade():
    op.drop_table('emails')
    op.drop_table('mail_accounts')
