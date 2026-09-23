from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Enum as SqlAlchemyEnum, ForeignKey, Integer, String
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.customer import Customer


class BookingState(str, Enum):
    SELECTED = "SELECTED"
    BOOKED = "BOOKED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class BookingStateTransitionInitiator(str, Enum):
    CLIENT = "client"
    SYSTEM = "system"
    HUMAN = "human"


class Booking(Base):
    """A customer booking and its current state."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    altegio_booking_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    master_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    services: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[BookingState] = mapped_column(
        SqlAlchemyEnum(
            BookingState,
            name="booking_state",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=BookingState.SELECTED,
        server_default=BookingState.SELECTED.value,
    )
    creation_channel: Mapped[str | None] = mapped_column(String(64))
    rescheduled_from_booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    customer: Mapped["Customer"] = relationship(back_populates="bookings")
    rescheduled_from: Mapped["Booking | None"] = relationship(
        remote_side="Booking.id", back_populates="rescheduled_to_bookings"
    )
    rescheduled_to_bookings: Mapped[list["Booking"]] = relationship(
        back_populates="rescheduled_from"
    )
    state_transitions: Mapped[list["BookingStateTransition"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )


class BookingStateTransition(Base):
    """An immutable record of a booking state change."""

    __tablename__ = "booking_state_transitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    from_state: Mapped[BookingState | None] = mapped_column(
        SqlAlchemyEnum(
            BookingState,
            name="booking_state",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=True,
    )
    to_state: Mapped[BookingState] = mapped_column(
        SqlAlchemyEnum(
            BookingState,
            name="booking_state",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
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

    booking: Mapped[Booking] = relationship(back_populates="state_transitions")
