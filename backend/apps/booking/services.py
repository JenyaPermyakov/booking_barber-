from decimal import Decimal
from datetime import datetime, time, timedelta

from django.utils import timezone
from django.db.models import Count, Max, Q, Sum

from .models import Booking
from .notifications.telegram import send_telegram_message
from .selectors import (
    REVENUE_BOOKING_STATUSES,
    get_active_bookings_for_date,
    get_bookings_for_analytics_period,
)
# логика создания слотов времени.

WORK_START_TIME = time(10, 0) # time start work
WORK_END_TIME = time(20, 0) # time finish work
SLOT_STEP = 30 # interval time
CANCEL_MIN_HOURS_BEFORE = 2
BOOKING_MIN_MINUTES_BEFORE = 30


class BookingCancellationError(Exception):
    pass


def get_booking_datetime(booking):
    return datetime.combine(
        booking.booking_date,
        booking.booking_time,
    )


def get_aware_datetime(booking_date, booking_time):
    booking_datetime = datetime.combine(booking_date, booking_time)

    if timezone.is_naive(booking_datetime):
        return timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone(),
        )

    return booking_datetime


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

    bookings = get_active_bookings_for_date(booking_date)

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

def get_available_slots(booking_date, service, min_start_datetime=None):

    available_slots = []

    slots = generate_working_time_slots(booking_date)

    work_end_datetime = datetime.combine(booking_date, WORK_END_TIME)

    for slot in slots:
        slot_start = datetime.combine(booking_date, slot)
        slot_end = slot_start + service.duration

        if slot_end > work_end_datetime:
            continue

        if min_start_datetime:
            aware_slot_start = get_aware_datetime(booking_date, slot)

            if aware_slot_start < min_start_datetime:
                continue

        if is_slot_available(
            booking_date=booking_date,
            booking_time=slot,
            service=service,
        ):
            available_slots.append(slot)

    return available_slots


def get_available_slots_payload(booking_date, service):
    min_start_datetime = timezone.localtime() + timedelta(
        minutes=BOOKING_MIN_MINUTES_BEFORE,
    )

    return [
        {
            "time": slot.strftime("%H:%M"),
        }
        for slot in get_available_slots(
            booking_date=booking_date,
            service=service,
            min_start_datetime=min_start_datetime,
        )
    ]


def get_booking_analytics(start_date, end_date):
    bookings = get_bookings_for_analytics_period(start_date, end_date)

    revenue_bookings = bookings.filter(status__in=REVENUE_BOOKING_STATUSES)
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
                filter=Q(status__in=REVENUE_BOOKING_STATUSES),
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


def confirm_booking(booking):
    booking.status = Booking.Status.CONFIRMED
    booking.save(update_fields=["status"])

    if booking.client.telegram_id:
        send_telegram_message(
            chat_id=booking.client.telegram_id,
            text=(
                f"✅ Ваша запись подтверждена!\n\n"
                f"Услуга: {booking.service.name}\n"
                f"Дата: {booking.booking_date}\n"
                f"Время: {booking.booking_time}"
            )
        )

    return booking


def cancel_booking_by_master(booking):
    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])

    if booking.client.telegram_id:
        send_telegram_message(
            chat_id=booking.client.telegram_id,
            text=(
                f"❌ Ваша запись была отменена мастером.\n\n"
                f"Услуга: {booking.service.name}\n"
                f"Дата: {booking.booking_date}\n"
                f"Время: {booking.booking_time}"
            )
        )

    return booking


def cancel_booking_by_client(booking):
    if booking.status == Booking.Status.CANCELLED:
        raise BookingCancellationError("Запись уже отменена.")

    booking_datetime = get_aware_datetime(
        booking.booking_date,
        booking.booking_time,
    )

    min_cancel_datetime = timezone.localtime() + timedelta(
        hours=CANCEL_MIN_HOURS_BEFORE,
    )

    if booking_datetime < min_cancel_datetime:
        raise BookingCancellationError(
            "Отменить запись можно минимум за 2 часа до начала."
        )

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])

    return booking


def update_booking_schedule(booking, booking_date, booking_time):
    booking.booking_date = booking_date
    booking.booking_time = booking_time
    booking.save(update_fields=["booking_date", "booking_time"])

    if booking.client.telegram_id:
        send_telegram_message(
            chat_id=booking.client.telegram_id,
            text=(
                f"🔄 Ваша запись была изменена.\n\n"
                f"Услуга: {booking.service.name}\n"
                f"Новая дата: {booking.booking_date}\n"
                f"Новое время: {booking.booking_time}"
            )
        )

    return booking
