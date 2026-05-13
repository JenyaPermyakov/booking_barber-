import pytest
from decimal import Decimal
from datetime import datetime
from datetime import timedelta
from django.utils import timezone

from apps.booking.models import Client, Service, Booking


@pytest.mark.django_db
def test_service_create():
    service = Service.objects.create(
        name="Стрижка + борода",
        price=13000,
        duration=timedelta(hours=1, minutes=30),
    )

    assert service.name == "Стрижка + борода"
    assert service.price == Decimal("13000")
    assert service.duration == timedelta(hours=1, minutes=30)


@pytest.mark.django_db
def test_service_str(service):
    assert str(service) == "Стрижка"


@pytest.mark.django_db
def test_client_create():
    client = Client.objects.create(
        name="Евгений",
        phone="77001112233",
        telegram_id=999888777,
    )

    assert client.name == "Евгений"
    assert client.phone == "77001112233"
    assert client.telegram_id == 999888777


@pytest.mark.django_db
def test_client_str(client_user):
    assert str(client_user) == "Тестовый клиент"


@pytest.mark.django_db
def test_booking_create(client_user, service):
    start_time = timezone.localtime() + timedelta(days=1)
    booking_time = start_time.time().replace(microsecond=0, tzinfo=None)

    booking = Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=start_time.date(),
        booking_time=booking_time,
        status=Booking.Status.PENDING,
    )

    assert booking.client == client_user
    assert booking.service == service
    assert booking.booking_date == start_time.date()
    assert booking.booking_time == booking_time
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
def test_booking_status_choices(booking):
    assert booking.status in [
        Booking.Status.PENDING,
        Booking.Status.CONFIRMED,
        Booking.Status.CANCELLED,
    ]


@pytest.mark.django_db
def test_booking_end_time_depends_on_service_duration(client_user, service):
    start_time = timezone.localtime() + timedelta(days=1)
    booking = Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=start_time.date(),
        booking_time=start_time.time().replace(microsecond=0, tzinfo=None),
        status=Booking.Status.PENDING,
    )
    booking_start = datetime.combine(booking.booking_date, booking.booking_time)
    booking_end = booking_start + booking.service.duration

    assert booking_end - booking_start == service.duration
