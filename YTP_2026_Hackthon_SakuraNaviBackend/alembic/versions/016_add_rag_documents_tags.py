"""add tags column to rag_documents

Revision ID: 010_add_rag_documents_tags
Revises: 009_create_rag_tables
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "010_add_rag_documents_tags"
down_revision = "009_create_rag_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rag_documents",
        sa.Column("tags", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("rag_documents", "tags")
