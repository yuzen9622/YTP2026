"""add address fields to users

Revision ID: 007_add_user_address_fields
Revises: 006_add_chat_conversation_deleted_at
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

revision = "007_add_user_address_fields"
down_revision = "006_add_chat_conversation_deleted_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("registered_address", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("residential_address", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_residential_same_as_registered",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_residential_same_as_registered")
    op.drop_column("users", "residential_address")
    op.drop_column("users", "registered_address")
