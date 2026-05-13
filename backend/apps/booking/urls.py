from django.urls import path

from .views import (
    ServiceListAPIView,
    AvailableSlotsAPIView,
    client_by_telegram,
    create_booking,
    my_booking,
    cancel_booking,
    master_schedule_view,
    barber_analytics_view,
    confirm_booking_view,
    cancel_booking_view,
    edit_booking_view,
)


urlpatterns = [
    path("services/", ServiceListAPIView.as_view(), name="service-list"),
    path("slots/", AvailableSlotsAPIView.as_view(), name="available-slots"),
    path("bookings/", create_booking, name="create_booking"),
    path("my-booking/", my_booking, name="my_booking"),
    path("clients/by-telegram/", client_by_telegram, name="client_by_telegram"),
    path("bookings/<int:pk>/", cancel_booking, name="cancel_booking_api"),

    path(
        "master/schedule/",
        master_schedule_view,
        name="master_schedule",
    ),

    path(
        "master/analytics/",
        barber_analytics_view,
        name="barber_analytics",
    ),

    path(
        "booking/<int:booking_id>/confirm/",
        confirm_booking_view,
        name="confirm_booking",
    ),

    path(
        "booking/<int:booking_id>/cancel/",
        cancel_booking_view,
        name="cancel_booking_master",
    ),

    path(
        "booking/<int:booking_id>/edit/",
        edit_booking_view,
        name="edit_booking"
    ),
]
