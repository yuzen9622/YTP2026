"""update users table: rename age to birth_date, add avatar_url and language_skills

Revision ID: 003_update_users_birth_date_avatar_languages
Revises: 002a_fix_alembic_version_width
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "003_update_users_birth_date_avatar_languages"
down_revision = "002a_fix_alembic_version_width"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop age column
    op.drop_column("users", "age")
    # Add new columns
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(512), nullable=True))
    op.add_column(
        "users",
        sa.Column("language_skills", postgresql.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "language_skills")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "birth_date")
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
