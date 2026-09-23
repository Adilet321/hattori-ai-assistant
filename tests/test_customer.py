import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.customer import Customer


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.mark.parametrize(
    "phone",
    [
        "8 777 123 45 67",
        "+7 (777) 123-45-67",
        "7 777 123 45 67",
    ],
)
def test_customer_is_created_with_normalized_phone(db_session: Session, phone: str) -> None:
    customer = Customer(phone=phone, name="Test customer")
    db_session.add(customer)
    db_session.commit()

    saved_customer = db_session.get(Customer, customer.id)

    assert saved_customer is not None
    assert saved_customer.phone == "+77771234567"
    assert saved_customer.visit_count == 0
    assert saved_customer.waitlist_enabled is False
    assert saved_customer.manual_intervention_active is False


def test_duplicate_normalized_phone_is_rejected(db_session: Session) -> None:
    db_session.add(Customer(phone="+7 (777) 123-45-67"))
    db_session.commit()

    db_session.add(Customer(phone="7 777 123 45 67"))

    with pytest.raises(IntegrityError):
        db_session.commit()
