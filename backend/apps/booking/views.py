from rest_framework.generics import ListAPIView
from .models import Service
from .selectors import get_active_services
from .serializers import ServiceSerializer


class ServiceListApiView(ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return get_active_services()