import pytest
from datetime import timedelta
from django.utils import timezone

from apps.booking.models import Client, Service, Booking


@pytest.fixture
def client_user(db):
    return Client.objects.create(
        name="Тестовый клиент",
        phone="77001234567",
        telegram_id=123456789,
    )


@pytest.fixture
def service(db):
    return Service.objects.create(
        name="Стрижка",
        price=8000,
        duration=timedelta(hours=1, minutes=15),
    )


@pytest.fixture
def future_start_time():
    return timezone.localtime() + timedelta(days=1, hours=1)


@pytest.fixture
def booking(db, client_user, service, future_start_time):
    return Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=future_start_time.date(),
        booking_time=future_start_time.time().replace(microsecond=0, tzinfo=None),
        status=Booking.Status.PENDING,
    )
