from rest_framework.generics import ListAPIView
from .models import Service
from .selectors import get_active_services
from .serializers import ServiceSerializer
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.booking.models import Service
from apps.booking.services import get_available_slots


class ServiceListApiView(ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return get_active_services()

class AvailableSlotsAPIView(APIView):
    def get(self, request):
        date_str = request.query_params.get("date")
        service_id = request.query_params.get("service_id")

        if not date_str:
            return Response(
                {"error": "Параметр date обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not service_id:
            return Response(
                {"error": "Параметр service_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используй YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return Response(
                {"error": "Услуга не найдена или неактивна"},
                status=status.HTTP_404_NOT_FOUND
            )

        slots = get_available_slots(
            booking_date=booking_date,
            service=service
        )

        return Response(
            {
                "date": booking_date,
                "service": service.name,
                "duration": str(service.duration),
                "slots": [slot.strftime("%H:%M") for slot in slots],
            },
            status=status.HTTP_200_OK
        )