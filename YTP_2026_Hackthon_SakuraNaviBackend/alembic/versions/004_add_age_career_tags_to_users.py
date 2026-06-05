"""Add age, career, tags columns to users table

Revision ID: e1f2a3b4c5d6
Revises: c9d4e2f1b5a8
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e1f2a3b4c5d6"
down_revision = "c9d4e2f1b5a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("age", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("career", sa.String(20), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "tags")
    op.drop_column("users", "career")
    op.drop_column("users", "age")
