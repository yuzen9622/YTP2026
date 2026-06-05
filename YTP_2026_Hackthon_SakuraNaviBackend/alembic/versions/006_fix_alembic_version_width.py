"""widen alembic_version version_num to support longer revision IDs

Revision ID: 002a_fix_alembic_version_width
Revises: 002_chat_tables
Create Date: 2026-04-25
"""

from alembic import op


revision = "002a_fix_alembic_version_width"
down_revision = "002_chat_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")


def downgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32)")
