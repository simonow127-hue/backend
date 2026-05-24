"""Initial tables: orders and analytics_events

Revision ID: 0001
Revises: 
Create Date: 2026-05-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_code", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("phone_raw", sa.Text(), nullable=False),
        sa.Column("phone_e164", sa.Text(), nullable=False),
        sa.Column("phone_digits_meta_snap", sa.Text(), nullable=False),
        sa.Column("phone_country", sa.Text(), nullable=True, server_default="MA"),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("subtotal_mad", sa.Integer(), nullable=False),
        sa.Column("shipping_mad", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_mad", sa.Integer(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=True, server_default="MAD"),
        sa.Column("upsell_added", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("payment_method", sa.Text(), nullable=True, server_default="COD"),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tracking", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("client_ip", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("event_id", sa.Text(), nullable=True),
        sa.Column("sheet_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_code"),
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("platform_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_orders_order_code", "orders", ["order_code"])
    op.create_index("ix_orders_phone_e164", "orders", ["phone_e164"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_analytics_events_event_id", "analytics_events", ["event_id"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("orders")
