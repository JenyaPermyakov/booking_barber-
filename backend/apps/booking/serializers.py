from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Client, Service, Booking


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "phone",
            "telegram_id",
        ]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "price",
            "duration",
        ]


class BookingSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(write_only=True)
    client_name = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)

    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source="service",
        write_only=True
    )

    client = ClientSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "client",
            "service",
            "service_id",
            "telegram_id",
            "client_name",
            "phone",
            "date",
            "time",
            "status",
        ]
        read_only_fields = [
            "id",
            "client",
            "service",
            "status",
        ]

    def validate(self, attrs):
        service = attrs["service"]
        date = attrs["date"]
        time = attrs["time"]
        telegram_id = attrs["telegram_id"]

        booking_datetime = datetime.combine(date, time)

        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(
                booking_datetime,
                timezone.get_current_timezone()
            )

        now = timezone.localtime()

        # Правило: запись минимум за 30 минут
        if booking_datetime < now + timedelta(minutes=30):
            raise serializers.ValidationError(
                "Запись можно создать минимум за 30 минут до начала."
            )

        # Правило: одна активная запись на пользователя
        active_booking_exists = Booking.objects.filter(
            client__telegram_id=telegram_id,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ]
        ).exists()

        if active_booking_exists:
            raise serializers.ValidationError(
                "У пользователя уже есть активная запись."
            )

        # Проверка занятости слота
        new_start = booking_datetime
        new_end = new_start + service.duration

        active_bookings = Booking.objects.filter(
            date=date,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ]
        )

        for booking in active_bookings:
            existing_start = datetime.combine(booking.date, booking.time)

            if timezone.is_naive(existing_start):
                existing_start = timezone.make_aware(
                    existing_start,
                    timezone.get_current_timezone()
                )

            existing_end = existing_start + booking.service.duration

            slot_is_busy = new_start < existing_end and new_end > existing_start

            if slot_is_busy:
                raise serializers.ValidationError(
                    "Выбранный слот уже занят."
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        telegram_id = validated_data.pop("telegram_id")
        client_name = validated_data.pop("client_name")
        phone = validated_data.pop("phone")

        client, created = Client.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "name": client_name,
                "phone": phone,
            }
        )

        if not created:
            client.name = client_name
            client.phone = phone
            client.save(update_fields=["name", "phone"])

        booking = Booking.objects.create(
            client=client,
            **validated_data
        )

        return booking