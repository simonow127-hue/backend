"""Admin analytics geo columns and IP cache

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analytics_events", sa.Column("client_ip", sa.Text(), nullable=True))
    op.add_column("analytics_events", sa.Column("geo_valid", sa.Boolean(), nullable=True))
    op.add_column("analytics_events", sa.Column("geo_reason", sa.Text(), nullable=True))

    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])
    op.create_index("ix_analytics_events_geo_valid", "analytics_events", ["geo_valid"])
    op.create_index("ix_analytics_events_event_name", "analytics_events", ["event_name"])

    op.create_table(
        "ip_geo_cache",
        sa.Column("ip", sa.Text(), nullable=False),
        sa.Column("country_iso", sa.Text(), nullable=True),
        sa.Column("is_valid_traffic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reason_code", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("ip"),
    )


def downgrade() -> None:
    op.drop_table("ip_geo_cache")
    op.drop_index("ix_analytics_events_event_name", table_name="analytics_events")
    op.drop_index("ix_analytics_events_geo_valid", table_name="analytics_events")
    op.drop_index("ix_analytics_events_created_at", table_name="analytics_events")
    op.drop_column("analytics_events", "geo_reason")
    op.drop_column("analytics_events", "geo_valid")
    op.drop_column("analytics_events", "client_ip")
