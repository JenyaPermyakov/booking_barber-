from django.urls import path

from .views import (
    ServiceListAPIView,
    AvailableSlotsAPIView,
    create_booking,
    my_booking,
    cancel_booking,
)


urlpatterns = [
    path("services/", ServiceListAPIView.as_view(), name="service-list"),
    path("slots/", AvailableSlotsAPIView.as_view(), name="available-slots"),
    path("bookings/", create_booking, name="create_booking"),
    path("my-booking/", my_booking, name="my_booking"),
    path("bookings/<int:pk>/", cancel_booking, name="cancel_booking"),
]