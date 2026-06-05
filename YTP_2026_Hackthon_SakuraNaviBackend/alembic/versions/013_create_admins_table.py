"""Create admins table — standalone admin credentials, no user link."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "010_create_admins_table"
down_revision = "009_add_user_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account", sa.String(50), nullable=False),
        sa.Column("hashed_password", sa.String(60), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account"),
    )
    op.create_index(op.f("ix_admins_account"), "admins", ["account"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_admins_account"), table_name="admins")
    op.drop_table("admins")