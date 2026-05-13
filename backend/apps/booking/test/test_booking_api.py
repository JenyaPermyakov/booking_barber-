import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.booking.models import Booking


def booking_payload(service, telegram_id, booking_datetime):
    return {
        "service_id": service.id,
        "telegram_id": telegram_id,
        "client_name": "Евгений",
        "phone": "77001112233",
        "booking_date": booking_datetime.date().isoformat(),
        "booking_time": (
            booking_datetime
            .time()
            .replace(microsecond=0, tzinfo=None)
            .isoformat()
        ),
    }


@pytest.mark.django_db
def test_create_booking_success(service):
    api_client = APIClient()

    start_time = timezone.localtime() + timedelta(days=1, hours=1)
    payload = booking_payload(service, 555666777, start_time)

    response = api_client.post(
        "/api/bookings/",
        payload,
        format="json",
    )

    assert response.status_code in [200, 201]

    assert Booking.objects.count() == 1

    booking = Booking.objects.first()

    assert booking.client.telegram_id == 555666777
    assert booking.service == service
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
def test_create_booking_minimum_30_minutes_rule(service):
    api_client = APIClient()

    start_time = timezone.localtime() + timedelta(minutes=10)
    payload = booking_payload(service, 111222333, start_time)

    response = api_client.post(
        "/api/bookings/",
        payload,
        format="json",
    )

    assert response.status_code == 400
    assert Booking.objects.count() == 0


@pytest.mark.django_db
def test_create_booking_one_active_booking_rule(client_user, service):
    api_client = APIClient()

    start_time = timezone.localtime() + timedelta(days=1, hours=1)

    Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=start_time.date(),
        booking_time=start_time.time().replace(microsecond=0, tzinfo=None),
        status=Booking.Status.PENDING,
    )

    second_start_time = start_time + timedelta(days=1)
    payload = booking_payload(service, client_user.telegram_id, second_start_time)

    response = api_client.post(
        "/api/bookings/",
        payload,
        format="json",
    )

    assert response.status_code == 400
    assert Booking.objects.count() == 1


@pytest.mark.django_db
def test_cancel_booking_success(booking):
    api_client = APIClient()

    response = api_client.delete(f"/api/bookings/{booking.id}/")

    assert response.status_code in [200, 204]

    booking.refresh_from_db()

    assert booking.status == Booking.Status.CANCELLED


@pytest.mark.django_db
def test_cancel_booking_minimum_2_hours_rule(client_user, service):
    api_client = APIClient()

    start_time = timezone.localtime() + timedelta(hours=1)

    booking = Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=start_time.date(),
        booking_time=start_time.time().replace(microsecond=0, tzinfo=None),
        status=Booking.Status.PENDING,
    )

    response = api_client.delete(f"/api/bookings/{booking.id}/")

    assert response.status_code == 400

    booking.refresh_from_db()

    assert booking.status != Booking.Status.CANCELLED
