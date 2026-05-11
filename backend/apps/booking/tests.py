from datetime import time, timedelta

from django.test import Client as TestClient
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Booking, Client, Service


@override_settings(ALLOWED_HOSTS=["127.0.0.1", "testserver"])
class BookingApiTests(TestCase):
    def setUp(self):
        self.api = TestClient(HTTP_HOST="127.0.0.1")
        self.service = Service.objects.create(
            name="Мужская стрижка",
            price="5000.00",
            duration=timedelta(hours=1),
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Иван",
            phone="87001234567",
            telegram_id=777,
        )
        self.booking = Booking.objects.create(
            client=self.client_obj,
            service=self.service,
            booking_date=timezone.localdate() + timedelta(days=1),
            booking_time=time(12, 0),
            status=Booking.Status.PENDING,
        )

    def test_my_booking_returns_active_booking(self):
        response = self.api.get(
            "/api/my-booking/",
            {
                "telegram_id": self.client_obj.telegram_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.booking.id)
        self.assertEqual(data["client"]["name"], self.client_obj.name)
        self.assertEqual(data["service"]["name"], self.service.name)

    def test_client_by_telegram_returns_saved_client(self):
        response = self.api.get(
            "/api/clients/by-telegram/",
            {
                "telegram_id": self.client_obj.telegram_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], self.client_obj.name)
        self.assertEqual(data["phone"], self.client_obj.phone)

    def test_cancel_booking_marks_booking_cancelled(self):
        response = self.api.delete(f"/api/bookings/{self.booking.id}/")

        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

        response = self.api.get(
            "/api/my-booking/",
            {
                "telegram_id": self.client_obj.telegram_id,
            },
        )
        self.assertEqual(response.status_code, 404)
