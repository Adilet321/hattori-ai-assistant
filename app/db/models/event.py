from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum as SqlAlchemyEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.booking import BookingStateTransitionInitiator

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.customer import Customer


class Event(Base):
    """An auditable event related to a customer, booking, or both."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    initiator: Mapped[BookingStateTransitionInitiator] = mapped_column(
        SqlAlchemyEnum(
            BookingStateTransitionInitiator,
            name="booking_state_transition_initiator",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )

    customer: Mapped["Customer | None"] = relationship(back_populates="events")
    booking: Mapped["Booking | None"] = relationship(back_populates="events")

