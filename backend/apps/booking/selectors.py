from .models import Booking, Client, Service


ACTIVE_BOOKING_STATUSES = [
    Booking.Status.PENDING,
    Booking.Status.CONFIRMED,
]

REVENUE_BOOKING_STATUSES = [
    Booking.Status.CONFIRMED,
    Booking.Status.COMPLETED,
]


def get_active_services():
    return Service.objects.filter(is_active=True).order_by("name")


def get_service_by_id(service_id):
    return Service.objects.filter(id=service_id).first()


def get_booking_by_id(booking_id):
    return (
        Booking.objects
        .select_related("client", "service")
        .filter(id=booking_id)
        .first()
    )


def get_master_bookings_for_date(selected_date):
    return (
        Booking.objects
        .filter(booking_date=selected_date)
        .select_related("client", "service")
        .order_by("booking_time")
    )


def get_active_booking_for_telegram_id(telegram_id):
    return (
        Booking.objects
        .filter(
            client__telegram_id=telegram_id,
            status__in=ACTIVE_BOOKING_STATUSES,
        )
        .select_related("client", "service")
        .order_by("booking_date", "booking_time")
        .first()
    )


def client_has_active_booking(telegram_id):
    return Booking.objects.filter(
        client__telegram_id=telegram_id,
        status__in=ACTIVE_BOOKING_STATUSES,
    ).exists()


def get_client_by_telegram_id(telegram_id):
    return Client.objects.filter(telegram_id=telegram_id).first()


def get_active_bookings_for_date(booking_date):
    return (
        Booking.objects
        .filter(
            booking_date=booking_date,
            status__in=ACTIVE_BOOKING_STATUSES,
        )
        .select_related("service")
    )


def get_bookings_for_analytics_period(start_date, end_date):
    return (
        Booking.objects
        .filter(booking_date__range=(start_date, end_date))
        .exclude(status=Booking.Status.CANCELLED)
        .select_related("client", "service")
    )
