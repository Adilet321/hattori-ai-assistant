from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.booking import (
    Booking,
    BookingState,
    BookingStateTransition,
    BookingStateTransitionInitiator,
)
from app.db.models.event import Event


class InvalidBookingStateTransition(ValueError):
    """Raised when a booking state transition is not allowed."""


_ALLOWED_TRANSITIONS: frozenset[tuple[BookingState, BookingState]] = frozenset(
    {
        (BookingState.SELECTED, BookingState.BOOKED),
        (BookingState.BOOKED, BookingState.CONFIRMED),
        (BookingState.BOOKED, BookingState.CANCELLED),
        (BookingState.BOOKED, BookingState.NO_SHOW),
        (BookingState.BOOKED, BookingState.COMPLETED),
        (BookingState.CONFIRMED, BookingState.CANCELLED),
        (BookingState.CONFIRMED, BookingState.NO_SHOW),
        (BookingState.CONFIRMED, BookingState.COMPLETED),
    }
)


class BookingService:
    """Apply booking lifecycle rules within the caller's transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def transition(
        self,
        booking: Booking,
        to_state: BookingState,
        initiator: BookingStateTransitionInitiator,
    ) -> Booking:
        booking = self._lock(booking)
        changed = self._apply_transition(booking, to_state, initiator)
        if changed:
            self.session.flush()
        return booking

    def reschedule(
        self,
        booking: Booking,
        *,
        master_identifier: str,
        services: list[dict[str, object]],
        starts_at: datetime,
        duration_minutes: int,
        initiator: BookingStateTransitionInitiator,
        creation_channel: str | None = None,
        altegio_booking_id: str | None = None,
    ) -> Booking:
        """Cancel an existing booking and create its replacement atomically."""
        booking = self._lock(booking)
        old_starts_at = booking.starts_at
        self._apply_transition(booking, BookingState.CANCELLED, initiator)

        replacement = Booking(
            altegio_booking_id=altegio_booking_id,
            customer=booking.customer,
            master_identifier=master_identifier,
            services=services,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            state=BookingState.BOOKED,
            creation_channel=creation_channel,
            rescheduled_from=booking,
        )
        self.session.add(replacement)
        self.session.flush()
        self.session.add(
            Event(
                event_type="booking.rescheduled",
                customer=booking.customer,
                booking=replacement,
                initiator=initiator,
                payload={
                    "old_booking_id": booking.id,
                    "new_booking_id": replacement.id,
                    "old_starts_at": old_starts_at.isoformat(),
                    "new_starts_at": replacement.starts_at.isoformat(),
                },
            )
        )
        self.session.flush()
        return replacement

    def _lock(self, booking: Booking) -> Booking:
        if booking.id is None:
            return booking

        statement = (
            select(Booking)
            .where(Booking.id == booking.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.execute(statement).scalar_one()

    def _apply_transition(
        self,
        booking: Booking,
        to_state: BookingState,
        initiator: BookingStateTransitionInitiator,
    ) -> bool:
        from_state = booking.state
        if from_state is to_state:
            return False

        if (from_state, to_state) not in _ALLOWED_TRANSITIONS:
            raise InvalidBookingStateTransition(
                f"Transition from {from_state.value} to {to_state.value} is not allowed"
            )

        booking.state = to_state
        booking.state_transitions.append(
            BookingStateTransition(
                from_state=from_state,
                to_state=to_state,
                initiator=initiator,
            )
        )
        self.session.add(
            Event(
                event_type="booking.state_changed",
                customer=booking.customer,
                booking=booking,
                initiator=initiator,
                payload={"from_state": from_state.value, "to_state": to_state.value},
            )
        )

        if to_state is BookingState.COMPLETED:
            booking.customer.visit_count += 1

        return True
