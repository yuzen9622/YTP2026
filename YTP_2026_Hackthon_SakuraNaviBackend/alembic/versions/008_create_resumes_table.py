"""create resumes table

Revision ID: 004_create_resumes_table
Revises: 003_update_users_birth_date_avatar_languages
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "004_create_resumes_table"
down_revision = "003_update_users_birth_date_avatar_languages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSON(), nullable=True),
        sa.Column("work_experiences", postgresql.JSON(), nullable=True),
        sa.Column("external_links", postgresql.JSON(), nullable=True),
        sa.Column("expected_salary_min", sa.Integer(), nullable=True),
        sa.Column("expected_salary_max", sa.Integer(), nullable=True),
        sa.Column("expected_salary_currency", sa.String(3), nullable=True),
        sa.Column("work_time_range", postgresql.JSON(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_resumes_user_id")
    op.drop_table("resumes")
