"""Token Family + encrypted phone storage

Revision ID: c9d4e2f1b5a8
Revises: a3f2c8d0e1b4
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c9d4e2f1b5a8"
down_revision = "a3f2c8d0e1b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # 1. Token Family: add family_id to refresh_tokens
    # ------------------------------------------------------------------
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,          # Initially nullable; back-filled below
        ),
    )
    # Back-fill existing tokens: assign each a unique family (one-token family)
    op.execute("UPDATE refresh_tokens SET family_id = gen_random_uuid() WHERE family_id IS NULL")
    # Now enforce NOT NULL and add index
    op.alter_column("refresh_tokens", "family_id", nullable=False)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    # ------------------------------------------------------------------
    # 2. Encrypted phone: widen phone column and add phone_hmac
    # ------------------------------------------------------------------
    # Widen the phone column to hold Fernet ciphertext (~256 chars max)
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(20),
        type_=sa.String(512),
        nullable=True,
    )
    op.add_column(
        "users",
        sa.Column("phone_hmac", sa.String(64), nullable=True),
    )
    op.create_index("ix_users_phone_hmac", "users", ["phone_hmac"], unique=True)

    # NOTE: Existing plaintext phone values must be encrypted and hashed
    # outside this migration using the application-level PhoneEncryptionService.
    # Run `alembic-migrate-phones` management command (or the provided script)
    # before removing the old plaintext values from backups.


def downgrade() -> None:
    # WARNING: Downgrading will drop encrypted phone data and the family_id
    # column.  Back up your data before running this in production.
    op.drop_index("ix_users_phone_hmac", table_name="users")
    op.drop_column("users", "phone_hmac")
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(512),
        type_=sa.String(20),
        nullable=True,
    )
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")
