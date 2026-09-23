import re
from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.booking import Booking


class Customer(Base):
    """Customer profile identified by a normalized phone number."""

    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("phone", name="uq_customers_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str | None] = mapped_column(String(32))
    first_contact_source: Mapped[str | None] = mapped_column(String(64))
    first_contact_channel: Mapped[str | None] = mapped_column(String(64))
    first_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    loyalty_status: Mapped[str | None] = mapped_column(String(64))
    customer_type: Mapped[str | None] = mapped_column(String(64))
    stop_status: Mapped[str | None] = mapped_column(String(64))
    stop_status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_status_original_text: Mapped[str | None] = mapped_column(Text)
    waitlist_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    waitlist_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manual_intervention_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")

    @validates("phone")
    def normalize_phone(self, _: str, value: str) -> str:
        """Store phone numbers in a canonical international format."""
        normalized = re.sub(r"\D", "", value)
        if not normalized:
            raise ValueError("Phone number must contain at least one digit")
        if len(normalized) == 11 and normalized.startswith("8"):
            normalized = f"7{normalized[1:]}"
        return f"+{normalized}"
