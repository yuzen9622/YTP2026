"""make email and phone nullable

Revision ID: a3f2c8d0e1b4
Revises: 7a1c9f0d4b32
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = "a3f2c8d0e1b4"
down_revision = "7a1c9f0d4b32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=True)
    op.alter_column("users", "phone", existing_type=sa.String(20), nullable=True)


def downgrade() -> None:
    # WARNING: rows with NULL email/phone will be set to an empty string.
    # Back up your data before running this downgrade in production.
    op.execute("UPDATE users SET email = '' WHERE email IS NULL")
    op.execute("UPDATE users SET phone = '' WHERE phone IS NULL")
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=False)
    op.alter_column("users", "phone", existing_type=sa.String(20), nullable=False)
