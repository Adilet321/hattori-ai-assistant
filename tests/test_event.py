from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.booking import Booking, BookingStateTransitionInitiator
from app.db.models.customer import Customer
from app.db.models.event import Event


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def create_customer(db_session: Session) -> Customer:
    customer = Customer(phone="+77771234567")
    db_session.add(customer)
    db_session.flush()
    return customer


def create_booking(db_session: Session, customer: Customer) -> Booking:
    booking = Booking(
        customer=customer,
        master_identifier="master-1",
        services=[],
        starts_at=datetime(2026, 9, 23, 10, 0, tzinfo=UTC),
        duration_minutes=60,
    )
    db_session.add(booking)
    db_session.flush()
    return booking


def test_event_is_created(db_session: Session) -> None:
    event = Event(
        event_type="customer.created",
        initiator=BookingStateTransitionInitiator.SYSTEM,
    )
    db_session.add(event)
    db_session.commit()

    saved_event = db_session.get(Event, event.id)

    assert saved_event is not None
    assert saved_event.event_type == "customer.created"


def test_event_can_be_related_to_customer(db_session: Session) -> None:
    customer = create_customer(db_session)
    event = Event(
        event_type="customer.updated",
        customer=customer,
        initiator=BookingStateTransitionInitiator.HUMAN,
    )
    db_session.add(event)
    db_session.commit()

    assert event.customer_id == customer.id
    assert event.customer is customer
    assert customer.events == [event]


def test_event_can_be_related_to_booking(db_session: Session) -> None:
    booking = create_booking(db_session, create_customer(db_session))
    event = Event(
        event_type="booking.created",
        booking=booking,
        initiator=BookingStateTransitionInitiator.SYSTEM,
    )
    db_session.add(event)
    db_session.commit()

    assert event.booking_id == booking.id
    assert event.booking is booking
    assert booking.events == [event]


def test_event_customer_and_booking_can_be_null(db_session: Session) -> None:
    event = Event(
        event_type="system.started",
        initiator=BookingStateTransitionInitiator.SYSTEM,
    )
    db_session.add(event)
    db_session.commit()

    assert event.customer_id is None
    assert event.booking_id is None


def test_event_payload_is_saved(db_session: Session) -> None:
    payload = {"source": "whatsapp", "metadata": {"message_id": "message-1"}}
    event = Event(
        event_type="message.received",
        initiator=BookingStateTransitionInitiator.CLIENT,
        payload=payload,
    )
    db_session.add(event)
    db_session.commit()

    assert db_session.get(Event, event.id).payload == payload


def test_event_initiator_is_saved(db_session: Session) -> None:
    event = Event(
        event_type="booking.cancelled",
        initiator=BookingStateTransitionInitiator.HUMAN,
    )
    db_session.add(event)
    db_session.commit()

    assert db_session.get(Event, event.id).initiator is BookingStateTransitionInitiator.HUMAN


def test_event_occurred_at_is_set_automatically(db_session: Session) -> None:
    event = Event(
        event_type="system.started",
        initiator=BookingStateTransitionInitiator.SYSTEM,
    )
    db_session.add(event)
    db_session.flush()

    assert event.occurred_at is not None

