"""Create bookings and booking state transitions.

Revision ID: 20260923_0002
Revises: 20260922_0001
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260923_0002"
down_revision: str | Sequence[str] | None = "20260922_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

booking_state = postgresql.ENUM(
    "SELECTED",
    "BOOKED",
    "CONFIRMED",
    "COMPLETED",
    "CANCELLED",
    "NO_SHOW",
    name="booking_state",
    create_type=False,
)
transition_initiator = postgresql.ENUM(
    "client", "system", "human", name="booking_state_transition_initiator", create_type=False
)


def upgrade() -> None:
    booking_state.create(op.get_bind(), checkfirst=False)
    transition_initiator.create(op.get_bind(), checkfirst=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("altegio_booking_id", sa.String(length=64), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("master_identifier", sa.String(length=128), nullable=False),
        sa.Column("services", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("state", booking_state, server_default="SELECTED", nullable=False),
        sa.Column("creation_channel", sa.String(length=64), nullable=True),
        sa.Column("rescheduled_from_booking_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["rescheduled_from_booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("altegio_booking_id", name="uq_bookings_altegio_booking_id"),
    )
    op.create_table(
        "booking_state_transitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("from_state", booking_state, nullable=True),
        sa.Column("to_state", booking_state, nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("initiator", transition_initiator, nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("booking_state_transitions")
    op.drop_table("bookings")
    transition_initiator.drop(op.get_bind(), checkfirst=False)
    booking_state.drop(op.get_bind(), checkfirst=False)

