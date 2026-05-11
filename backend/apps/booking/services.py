from datetime import datetime, time, timedelta
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