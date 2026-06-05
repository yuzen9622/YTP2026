"""Create customer service tickets and messages tables."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "011_create_customer_service_tables"
down_revision = "010_create_admins_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_service_tickets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("assigned_admin_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
        sa.Column("previous_ticket_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.String(10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["admins.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["previous_ticket_id"], ["customer_service_tickets.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_customer_service_tickets_user_id"), "customer_service_tickets", ["user_id"])
    op.create_index(op.f("ix_customer_service_tickets_assigned_admin_id"), "customer_service_tickets", ["assigned_admin_id"])
    op.create_index(op.f("ix_customer_service_tickets_status"), "customer_service_tickets", ["status"])

    op.create_table(
        "customer_service_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("sender_type", sa.String(10), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["ticket_id"], ["customer_service_tickets.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_customer_service_messages_ticket_id"), "customer_service_messages", ["ticket_id"])
    op.create_index(op.f("ix_customer_service_messages_sender_id"), "customer_service_messages", ["sender_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_customer_service_messages_sender_id"), table_name="customer_service_messages")
    op.drop_index(op.f("ix_customer_service_messages_ticket_id"), table_name="customer_service_messages")
    op.drop_table("customer_service_messages")
    op.drop_index(op.f("ix_customer_service_tickets_status"), table_name="customer_service_tickets")
    op.drop_index(op.f("ix_customer_service_tickets_assigned_admin_id"), table_name="customer_service_tickets")
    op.drop_index(op.f("ix_customer_service_tickets_user_id"), table_name="customer_service_tickets")
    op.drop_table("customer_service_tickets")