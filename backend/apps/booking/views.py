from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booking, Client, Service
from .serializers import BookingSerializer, ClientSerializer, ServiceSerializer
from datetime import date
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.shortcuts import redirect, get_object_or_404

def master_schedule_view(request):
    selected_date_str = request.GET.get("date")

    if selected_date_str:
        selected_date = parse_date(selected_date_str)
    else:
        selected_date = date.today()

    bookings = (
        Booking.objects
        .filter(booking_date=selected_date)
        .select_related("client", "service")
        .order_by("booking_time")
    )

    context = {
        "selected_date": selected_date,
        "bookings": bookings,
    }

    return render(request, "booking/master_schedule.html", context)


def confirm_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    booking.status = "confirmed"
    booking.save()

    return redirect("master_schedule")


def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    booking.status = "cancelled"
    booking.save()

    return redirect("master_schedule")

class ServiceListAPIView(ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class AvailableSlotsAPIView(APIView):
    def get(self, request):
        date_str = request.query_params.get("date")
        service_id = request.query_params.get("service_id")

        if not date_str:
            return Response(
                {"error": "date обязателен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not service_id:
            return Response(
                {"error": "service_id обязателен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response(
                {"error": "Услуга не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        work_start = datetime.combine(selected_date, datetime.strptime("10:00", "%H:%M").time())
        work_end = datetime.combine(selected_date, datetime.strptime("20:00", "%H:%M").time())

        if timezone.is_naive(work_start):
            work_start = timezone.make_aware(work_start, timezone.get_current_timezone())

        if timezone.is_naive(work_end):
            work_end = timezone.make_aware(work_end, timezone.get_current_timezone())

        now = timezone.localtime()

        slots = []
        current_time = work_start

        while current_time + service.duration <= work_end:
            slot_end = current_time + service.duration

            is_past = current_time < now + timedelta(minutes=30)

            is_busy = Booking.objects.filter(
                booking_date=selected_date,
                status__in=[
                    Booking.Status.PENDING,
                    Booking.Status.CONFIRMED,
                ],
                booking_time__lt=slot_end.time(),
            ).filter(
                booking_time__gte=current_time.time()
            ).exists()

            if not is_past and not is_busy:
                slots.append({
                    "time": current_time.strftime("%H:%M")
                })

            current_time += timedelta(minutes=30)

        return Response(slots)


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
    ).order_by("booking_date", "booking_time").first()

    if not booking:
        return Response(
            {
                "detail": "Активная запись не найдена."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = BookingSerializer(booking)
    return Response(serializer.data)


@api_view(["GET"])
def client_by_telegram(request):
    telegram_id = request.query_params.get("telegram_id")

    if not telegram_id:
        return Response(
            {
                "error": "telegram_id обязателен."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        client = Client.objects.get(telegram_id=telegram_id)
    except Client.DoesNotExist:
        return Response(
            {
                "detail": "Клиент не найден."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ClientSerializer(client)
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

    booking_datetime = datetime.combine(
        booking.booking_date,
        booking.booking_time
    )

    if timezone.is_naive(booking_datetime):
        booking_datetime = timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone()
        )

    now = timezone.localtime()

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
