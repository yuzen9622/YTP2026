"""Add role column to users table."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "009_add_user_role"
down_revision = "008_add_user_gender"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
