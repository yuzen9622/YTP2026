"""add deleted_at to chat_conversations

Revision ID: 006_add_chat_conversation_deleted_at
Revises: 005_create_knowledge_tables
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_add_chat_conversation_deleted_at"
down_revision = "004_create_resumes_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_conversations",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_conversations", "deleted_at")
