from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer


@api_view(["POST"])
def create_booking(request):
    serializer = BookingSerializer(data=request.data)

    if serializer.is_valid():
        booking = serializer.save()
        response_serializer = BookingSerializer(booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["GET"])
def my_booking(request):
    telegram_id = request.query_params.get("telegram_id")

    if not telegram_id:
        return Response(
            {
                "error": "telegram_id обязателен."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking = Booking.objects.filter(
        client__telegram_id=telegram_id,
        status__in=[
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
        ]
    ).order_by("date", "time").first()

    if not booking:
        return Response(
            {
                "detail": "Активная запись не найдена."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = BookingSerializer(booking)
    return Response(serializer.data)


@api_view(["DELETE"])
def cancel_booking(request, pk):
    try:
        booking = Booking.objects.get(pk=pk)
    except Booking.DoesNotExist:
        return Response(
            {
                "error": "Запись не найдена."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if booking.status == Booking.Status.CANCELLED:
        return Response(
            {
                "error": "Запись уже отменена."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking_datetime = datetime.combine(booking.date, booking.time)

    if timezone.is_naive(booking_datetime):
        booking_datetime = timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone()
        )

    now = timezone.localtime()

    # Правило: отмена минимум за 2 часа
    if booking_datetime < now + timedelta(hours=2):
        return Response(
            {
                "error": "Отменить запись можно минимум за 2 часа до начала."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])

    return Response(
        {
            "detail": "Запись успешно отменена."
        },
        status=status.HTTP_200_OK
    )