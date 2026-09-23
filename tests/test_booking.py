from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.booking import (
    Booking,
    BookingState,
    BookingStateTransition,
    BookingStateTransitionInitiator,
)
from app.db.models.customer import Customer


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def create_customer(db_session: Session, phone: str = "+77771234567") -> Customer:
    customer = Customer(phone=phone)
    db_session.add(customer)
    db_session.flush()
    return customer


def create_booking(db_session: Session, **kwargs: object) -> Booking:
    defaults: dict[str, object] = {
        "master_identifier": "master-1",
        "services": [],
        "starts_at": datetime(2026, 9, 23, 10, 0, tzinfo=UTC),
        "duration_minutes": 60,
    }
    if "customer" not in kwargs:
        defaults["customer"] = create_customer(db_session)
    defaults.update(kwargs)
    booking = Booking(**defaults)
    db_session.add(booking)
    db_session.flush()
    return booking


def test_booking_can_be_created_in_selected_state(db_session: Session) -> None:
    booking = create_booking(db_session)

    assert booking.state is BookingState.SELECTED


def test_booking_is_related_to_customer(db_session: Session) -> None:
    customer = create_customer(db_session)
    booking = create_booking(db_session, customer=customer)

    assert booking.customer_id == customer.id
    assert booking.customer is customer
    assert customer.bookings == [booking]


def test_duplicate_altegio_booking_id_is_rejected(db_session: Session) -> None:
    create_booking(db_session, altegio_booking_id="altegio-123")

    with pytest.raises(IntegrityError):
        create_booking(
            db_session,
            altegio_booking_id="altegio-123",
            customer=create_customer(db_session, phone="+77771234568"),
        )


def test_booking_state_transition_is_saved(db_session: Session) -> None:
    booking = create_booking(db_session)
    transition = BookingStateTransition(
        booking=booking,
        from_state=BookingState.SELECTED,
        to_state=BookingState.BOOKED,
        initiator=BookingStateTransitionInitiator.CLIENT,
    )
    db_session.add(transition)
    db_session.commit()

    saved_transition = db_session.get(BookingStateTransition, transition.id)

    assert saved_transition is not None
    assert saved_transition.booking_id == booking.id
    assert saved_transition.from_state is BookingState.SELECTED
    assert saved_transition.to_state is BookingState.BOOKED
    assert saved_transition.initiator is BookingStateTransitionInitiator.CLIENT


def test_rescheduled_booking_can_reference_previous_booking(db_session: Session) -> None:
    previous_booking = create_booking(db_session)
    rescheduled_booking = create_booking(
        db_session,
        customer=previous_booking.customer,
        rescheduled_from=previous_booking,
    )
    db_session.commit()

    assert rescheduled_booking.rescheduled_from_booking_id == previous_booking.id
    assert previous_booking.rescheduled_to_bookings == [rescheduled_booking]
