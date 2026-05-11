from django.urls import path
from .views import ServiceListApiView
from apps.booking.views import AvailableSlotsAPIView


urlpatterns = [

    path("services/", ServiceListApiView.as_view(), name="service-list"),
    path("slots/", AvailableSlotsAPIView.as_view(), name="available-slots"),

]