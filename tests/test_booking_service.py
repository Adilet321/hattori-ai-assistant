from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.booking import (
    Booking,
    BookingState,
    BookingStateTransition,
    BookingStateTransitionInitiator,
)
from app.db.models.customer import Customer
from app.db.models.event import Event
from app.services.booking import BookingService, InvalidBookingStateTransition


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture
def selected_booking(db_session: Session) -> Booking:
    customer = Customer(phone="+77771234567")
    booking = Booking(
        customer=customer,
        master_identifier="master-1",
        services=[{"identifier": "service-1"}],
        starts_at=datetime(2026, 9, 23, 10, 0, tzinfo=UTC),
        duration_minutes=60,
        state=BookingState.SELECTED,
        creation_channel="whatsapp",
    )
    db_session.add(booking)
    db_session.commit()
    return booking


def transition_count(db_session: Session) -> int:
    return db_session.scalar(select(func.count()).select_from(BookingStateTransition)) or 0


def event_count(db_session: Session) -> int:
    return db_session.scalar(select(func.count()).select_from(Event)) or 0


def book(db_session: Session, booking: Booking) -> Booking:
    return BookingService(db_session).transition(
        booking,
        BookingState.BOOKED,
        BookingStateTransitionInitiator.CLIENT,
    )


def test_selected_can_transition_to_booked(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)

    assert booking.state is BookingState.BOOKED
    assert event_count(db_session) == 1

    event = db_session.scalar(select(Event).where(Event.booking_id == booking.id))

    assert event is not None
    assert event.event_type == "booking.state_changed"
    assert event.customer is booking.customer
    assert event.booking is booking
    assert event.payload == {"from_state": "SELECTED", "to_state": "BOOKED"}


def test_booked_can_transition_to_confirmed(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)

    BookingService(db_session).transition(
        booking,
        BookingState.CONFIRMED,
        BookingStateTransitionInitiator.SYSTEM,
    )

    assert booking.state is BookingState.CONFIRMED


def test_booked_to_completed_increments_visit_count(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)

    BookingService(db_session).transition(
        booking,
        BookingState.COMPLETED,
        BookingStateTransitionInitiator.HUMAN,
    )

    assert booking.customer.visit_count == 1
    event = db_session.scalar(
        select(Event).where(
            Event.booking_id == booking.id,
            Event.event_type == "booking.state_changed",
            Event.payload["to_state"].as_string() == "COMPLETED",
        )
    )
    assert event is not None


def test_repeated_completed_does_not_increment_visit_count_twice(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)
    service = BookingService(db_session)
    service.transition(
        booking,
        BookingState.COMPLETED,
        BookingStateTransitionInitiator.SYSTEM,
    )
    transitions_after_completion = transition_count(db_session)
    events_after_completion = event_count(db_session)

    service.transition(
        booking,
        BookingState.COMPLETED,
        BookingStateTransitionInitiator.SYSTEM,
    )

    assert booking.customer.visit_count == 1
    assert transition_count(db_session) == transitions_after_completion
    assert event_count(db_session) == events_after_completion


@pytest.mark.parametrize("terminal_state", [BookingState.CANCELLED, BookingState.NO_SHOW])
def test_non_completed_terminal_state_does_not_increment_visit_count(
    db_session: Session,
    selected_booking: Booking,
    terminal_state: BookingState,
) -> None:
    booking = book(db_session, selected_booking)

    BookingService(db_session).transition(
        booking,
        terminal_state,
        BookingStateTransitionInitiator.HUMAN,
    )

    assert booking.customer.visit_count == 0
    if terminal_state is BookingState.CANCELLED:
        event = db_session.scalar(
            select(Event).where(
                Event.booking_id == booking.id,
                Event.event_type == "booking.state_changed",
                Event.payload["to_state"].as_string() == "CANCELLED",
            )
        )
        assert event is not None


def test_disallowed_transition_raises_clear_error(
    db_session: Session, selected_booking: Booking
) -> None:
    with pytest.raises(
        InvalidBookingStateTransition,
        match="Transition from SELECTED to COMPLETED is not allowed",
    ):
        BookingService(db_session).transition(
            selected_booking,
            BookingState.COMPLETED,
            BookingStateTransitionInitiator.SYSTEM,
        )

    assert selected_booking.state is BookingState.SELECTED
    assert transition_count(db_session) == 0


def test_reschedule_cancels_old_booking_and_creates_linked_booked_replacement(
    db_session: Session, selected_booking: Booking
) -> None:
    old_booking = book(db_session, selected_booking)

    replacement = BookingService(db_session).reschedule(
        old_booking,
        master_identifier="master-2",
        services=[{"identifier": "service-2"}],
        starts_at=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        duration_minutes=45,
        initiator=BookingStateTransitionInitiator.CLIENT,
        creation_channel="whatsapp",
    )

    assert old_booking.state is BookingState.CANCELLED
    assert replacement.state is BookingState.BOOKED
    assert replacement.customer_id == old_booking.customer_id
    assert replacement.rescheduled_from_booking_id == old_booking.id
    assert old_booking.customer.visit_count == 0
    assert event_count(db_session) == 3

    event = db_session.scalar(
        select(Event).where(
            Event.booking_id == replacement.id,
            Event.event_type == "booking.rescheduled",
        )
    )

    assert event is not None
    assert event.customer is old_booking.customer
    assert event.booking is replacement
    assert event.payload["old_booking_id"] == old_booking.id
    assert event.payload["new_booking_id"] == replacement.id
    assert event.payload["old_starts_at"] == old_booking.starts_at.isoformat()
    assert event.payload["new_starts_at"] == replacement.starts_at.isoformat()


def test_transition_history_contains_state_time_and_initiator(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)

    transition = db_session.scalar(
        select(BookingStateTransition).where(BookingStateTransition.booking_id == booking.id)
    )

    assert transition is not None
    assert transition.from_state is BookingState.SELECTED
    assert transition.to_state is BookingState.BOOKED
    assert transition.changed_at is not None
    assert transition.initiator is BookingStateTransitionInitiator.CLIENT


def test_repeated_same_state_does_not_create_duplicate_transition(
    db_session: Session, selected_booking: Booking
) -> None:
    booking = book(db_session, selected_booking)
    transitions_after_booking = transition_count(db_session)
    events_after_booking = event_count(db_session)

    BookingService(db_session).transition(
        booking,
        BookingState.BOOKED,
        BookingStateTransitionInitiator.CLIENT,
    )

    assert transition_count(db_session) == transitions_after_booking
    assert event_count(db_session) == events_after_booking
