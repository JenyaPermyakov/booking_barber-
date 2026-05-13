from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BookingSerializer, ClientSerializer, ServiceSerializer
from .selectors import (
    get_active_booking_for_telegram_id,
    get_active_services,
    get_booking_by_id,
    get_client_by_telegram_id,
    get_master_bookings_for_date,
    get_service_by_id,
)
from .services import (
    BookingCancellationError,
    cancel_booking_by_client,
    cancel_booking_by_master,
    confirm_booking,
    get_available_slots_payload,
    get_booking_analytics,
    update_booking_schedule,
)

def master_schedule_view(request):
    selected_date_str = request.GET.get("date")

    selected_date = parse_date(selected_date_str or "") or timezone.localdate()
    bookings = get_master_bookings_for_date(selected_date)

    context = {
        "selected_date": selected_date,
        "bookings": bookings,
    }

    return render(request, "booking/master_schedule.html", context)


def barber_analytics_view(request):
    today = timezone.localdate()
    default_start_date = today.replace(day=1)

    start_date = parse_date(request.GET.get("start_date") or "")
    end_date = parse_date(request.GET.get("end_date") or "")

    if not start_date:
        start_date = default_start_date

    if not end_date:
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    analytics = get_booking_analytics(
        start_date=start_date,
        end_date=end_date,
    )

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "analytics": analytics,
    }

    return render(request, "booking/analytics.html", context)


def confirm_booking_view(request, booking_id):
    booking = get_booking_by_id(booking_id)

    if not booking:
        raise Http404("Запись не найдена.")

    confirm_booking(booking)

    return redirect("master_schedule")


def cancel_booking_view(request, booking_id):
    booking = get_booking_by_id(booking_id)

    if not booking:
        raise Http404("Запись не найдена.")

    cancel_booking_by_master(booking)

    return redirect("master_schedule")

class ServiceListAPIView(ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return get_active_services()


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

        selected_date = parse_date(date_str)

        if not selected_date:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service_id = int(service_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "service_id должен быть числом."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = get_service_by_id(service_id)

        if not service:
            return Response(
                {"error": "Услуга не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(get_available_slots_payload(selected_date, service))


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

    booking = get_active_booking_for_telegram_id(telegram_id)

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

    client = get_client_by_telegram_id(telegram_id)

    if not client:
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
    booking = get_booking_by_id(pk)

    if not booking:
        return Response(
            {
                "error": "Запись не найдена."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        cancel_booking_by_client(booking)
    except BookingCancellationError as error:
        return Response(
            {
                "error": str(error)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            "detail": "Запись успешно отменена."
        },
        status=status.HTTP_200_OK
    )

def edit_booking_view(request, booking_id):
    booking = get_booking_by_id(booking_id)

    if not booking:
        raise Http404("Запись не найдена.")

    if request.method == "POST":
        booking_date = parse_date(request.POST.get("booking_date") or "")
        booking_time = parse_time(request.POST.get("booking_time") or "")

        if booking_date and booking_time:
            update_booking_schedule(
                booking=booking,
                booking_date=booking_date,
                booking_time=booking_time,
            )

        return redirect("master_schedule")

    return render(
        request,
        "booking/edit_booking.html",
        {
            "booking": booking
        }
    )
