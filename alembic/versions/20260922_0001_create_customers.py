"""Create customers table.

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260922_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("first_contact_source", sa.String(length=64), nullable=True),
        sa.Column("first_contact_channel", sa.String(length=64), nullable=True),
        sa.Column("first_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("loyalty_status", sa.String(length=64), nullable=True),
        sa.Column("customer_type", sa.String(length=64), nullable=True),
        sa.Column("stop_status", sa.String(length=64), nullable=True),
        sa.Column("stop_status_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stop_status_original_text", sa.Text(), nullable=True),
        sa.Column("waitlist_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("waitlist_reminder_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_intervention_active", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_customers_phone"),
    )


def downgrade() -> None:
    op.drop_table("customers")

