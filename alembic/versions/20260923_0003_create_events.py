"""Create events table.

Revision ID: 20260923_0003
Revises: 20260923_0002
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260923_0003"
down_revision: str | Sequence[str] | None = "20260923_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

initiator = postgresql.ENUM(
    "client", "system", "human", name="booking_state_transition_initiator", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("initiator", initiator, nullable=False),
        sa.Column("payload", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("events")

