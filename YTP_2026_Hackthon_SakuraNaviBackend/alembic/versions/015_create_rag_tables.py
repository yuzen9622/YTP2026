"""create rag_documents and rag_chunks tables (numpy cosine similarity, no pgvector extension)

Revision ID: 009_create_rag_tables
Revises: 008_add_user_gender
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "009_create_rag_tables"
down_revision = "011_create_customer_service_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "rag_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename", name="uq_rag_documents_filename"),
    )
    op.create_index("ix_rag_documents_filename", "rag_documents", ["filename"])
    op.create_index("ix_rag_documents_category", "rag_documents", ["category"])

    op.create_table(
        "rag_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=300), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("tsv_content", postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    op.execute(
        "CREATE INDEX ix_rag_chunks_tsv ON rag_chunks USING GIN (tsv_content)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rag_chunks_tsv")
    op.execute("DROP INDEX IF EXISTS ix_rag_chunks_embedding")
    op.drop_index("ix_rag_chunks_document_id", table_name="rag_chunks")
    op.drop_table("rag_chunks")
    op.drop_index("ix_rag_documents_category", table_name="rag_documents")
    op.drop_index("ix_rag_documents_filename", table_name="rag_documents")
    op.drop_table("rag_documents")
