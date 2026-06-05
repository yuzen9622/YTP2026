"""Add gender column to users table."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "008_add_user_gender"
down_revision = "007_add_user_address_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("gender", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "gender")