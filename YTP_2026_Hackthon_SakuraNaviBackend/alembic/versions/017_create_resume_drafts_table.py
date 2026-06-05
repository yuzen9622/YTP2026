"""create resume_drafts table

Revision ID: 011_create_resume_drafts_table
Revises: 010_add_rag_documents_tags
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "011_create_resume_drafts_table"
down_revision = "010_add_rag_documents_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload_json", postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("current_step", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_drafts_user_id", "resume_drafts", ["user_id"], unique=False)
    op.create_index(
        "ix_resume_drafts_conversation_id",
        "resume_drafts",
        ["conversation_id"],
        unique=False,
    )
    op.create_index("ix_resume_drafts_status", "resume_drafts", ["status"], unique=False)
    op.create_index(
        "uq_resume_drafts_active_user_conversation",
        "resume_drafts",
        ["user_id", "conversation_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_resume_drafts_active_user_conversation", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_status", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_conversation_id", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_user_id", table_name="resume_drafts")
    op.drop_table("resume_drafts")
