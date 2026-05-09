from django.contrib import admin
from .models import Client, Service, Booking

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'telegram_id',)
    search_fields = ('name', 'phone',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'duration',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service','booking_date', 'booking_time', 'status',)
    list_filter = ('status', 'booking_date',)
    search_fields = ('client__name',)

# Register your models here.
