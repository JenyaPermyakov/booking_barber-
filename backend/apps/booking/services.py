from decimal import Decimal
from datetime import datetime, time, timedelta

from django.db.models import Count, Max, Q, Sum

from apps.booking.models import Booking
# логика создания слотов времени.

WORK_START_TIME = time(10, 0) # time start work
WORK_END_TIME = time(20, 0) # time finish work
SLOT_STEP = 30 # interval time


def generate_working_time_slots(
    date,
    start_time=WORK_START_TIME,
    end_time=WORK_END_TIME,
    step_minutes=SLOT_STEP,
):
    slots = []

    current_datetime = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)

    while current_datetime < end_datetime:
        slots.append(current_datetime.time())
        current_datetime += timedelta(minutes=step_minutes)

    return slots

def has_booking_overlap(booking_date, booking_time, duration):

    new_start = datetime.combine(booking_date, booking_time)
    new_end = new_start + duration

    bookings = Booking.objects.filter(
        booking_date=booking_date
    ).exclude(
        status=Booking.Status.CANCELLED
    )

    for booking in bookings:
        existing_start = datetime.combine(
            booking.booking_date,
            booking.booking_time
        )
        existing_end = existing_start + booking.service.duration

        if new_start < existing_end and new_end > existing_start:
            return True

    return False

def is_slot_available(booking_date, booking_time, service):

    return not has_booking_overlap(
        booking_date=booking_date,
        booking_time=booking_time,
        duration=service.duration,
    )

def get_available_slots(booking_date, service):

    available_slots = []

    slots = generate_working_time_slots(booking_date)

    work_end_datetime = datetime.combine(booking_date, WORK_END_TIME)

    for slot in slots:
        slot_start = datetime.combine(booking_date, slot)
        slot_end = slot_start + service.duration

        if slot_end > work_end_datetime:
            continue

        if is_slot_available(
            booking_date=booking_date,
            booking_time=slot,
            service=service,
        ):
            available_slots.append(slot)

    return available_slots


def get_booking_analytics(start_date, end_date):
    bookings = (
        Booking.objects
        .filter(booking_date__range=(start_date, end_date))
        .exclude(status=Booking.Status.CANCELLED)
        .select_related("client", "service")
    )

    revenue_statuses = [
        Booking.Status.CONFIRMED,
        Booking.Status.COMPLETED,
    ]

    revenue_bookings = bookings.filter(status__in=revenue_statuses)
    revenue = (
        revenue_bookings.aggregate(total=Sum("service__price"))["total"]
        or Decimal("0.00")
    )
    paid_bookings_count = revenue_bookings.count()

    if paid_bookings_count:
        average_check = revenue / paid_bookings_count
    else:
        average_check = Decimal("0.00")

    top_services = []
    for service in (
        revenue_bookings
        .values("service__name")
        .annotate(
            bookings_count=Count("id"),
            revenue=Sum("service__price"),
        )
        .order_by("-revenue", "-bookings_count", "service__name")
    ):
        top_services.append({
            "name": service["service__name"],
            "bookings_count": service["bookings_count"],
            "revenue": service["revenue"] or Decimal("0.00"),
        })

    clients = []
    for client in (
        bookings
        .values("client__name", "client__phone")
        .annotate(
            bookings_count=Count("id"),
            revenue=Sum(
                "service__price",
                filter=Q(status__in=revenue_statuses),
            ),
            last_booking_date=Max("booking_date"),
        )
        .order_by("client__name", "client__phone")
    ):
        clients.append({
            "name": client["client__name"],
            "phone": client["client__phone"],
            "bookings_count": client["bookings_count"],
            "revenue": client["revenue"] or Decimal("0.00"),
            "last_booking_date": client["last_booking_date"],
        })

    return {
        "bookings_count": bookings.count(),
        "paid_bookings_count": paid_bookings_count,
        "revenue": revenue,
        "average_check": average_check,
        "top_services": top_services,
        "clients": clients,
        "clients_count": len(clients),
    }
