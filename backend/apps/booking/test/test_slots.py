import pytest
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.booking.models import Booking
from apps.booking.services import (
    generate_working_time_slots,
    get_available_slots,
)


@pytest.mark.django_db
def test_available_slots_endpoint_returns_200(service):
    api_client = APIClient()

    date = (timezone.now() + timedelta(days=1)).date()

    response = api_client.get(
        "/api/slots/",
        {
            "date": date.isoformat(),
            "service_id": service.id,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_available_slots_endpoint_requires_date(service):
    api_client = APIClient()

    response = api_client.get(
        "/api/slots/",
        {
            "service_id": service.id,
        },
    )

    assert response.status_code in [400, 422]


@pytest.mark.django_db
def test_available_slots_endpoint_requires_service_id():
    api_client = APIClient()

    date = (timezone.now() + timedelta(days=1)).date()

    response = api_client.get(
        "/api/slots/",
        {
            "date": date.isoformat(),
        },
    )

    assert response.status_code in [400, 422]


@pytest.mark.django_db
def test_generate_working_time_slots_returns_workday_slots():
    date = timezone.localdate() + timedelta(days=1)

    slots = generate_working_time_slots(date)

    assert len(slots) == 20
    assert slots[0].strftime("%H:%M") == "10:00"
    assert slots[-1].strftime("%H:%M") == "19:30"


@pytest.mark.django_db
def test_get_available_slots_respects_service_duration(service):
    date = timezone.localdate() + timedelta(days=1)

    slots = get_available_slots(date, service)

    assert slots
    assert slots[-1].strftime("%H:%M") == "18:30"


@pytest.mark.django_db
def test_busy_slot_is_not_available(client_user, service):
    api_client = APIClient()

    date = (timezone.now() + timedelta(days=1)).date()

    first_response = api_client.get(
        "/api/slots/",
        {
            "date": date.isoformat(),
            "service_id": service.id,
        },
    )

    assert first_response.status_code == 200

    slots = first_response.json()

    if not slots:
        pytest.skip("Нет доступных слотов для проверки занятости")

    first_slot = slots[0]

    start_time = first_slot.get("start_time") or first_slot.get("time")

    assert start_time is not None

    if "T" in start_time:
        start_datetime = datetime.fromisoformat(start_time)
        booking_date = start_datetime.date()
        booking_time = start_datetime.time().replace(microsecond=0)
    else:
        booking_date = date
        booking_time = datetime.strptime(start_time, "%H:%M").time()

    Booking.objects.create(
        client=client_user,
        service=service,
        booking_date=booking_date,
        booking_time=booking_time,
        status=Booking.Status.PENDING,
    )

    second_response = api_client.get(
        "/api/slots/",
        {
            "date": date.isoformat(),
            "service_id": service.id,
        },
    )

    assert second_response.status_code == 200

    new_slots = second_response.json()

    assert first_slot not in new_slots
