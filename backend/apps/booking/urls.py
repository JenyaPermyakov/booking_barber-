from django.urls import path

from .views import ServiceListApiView


urlpatterns = [

    path("services/", ServiceListApiView.as_view(), name="service-list"),

]