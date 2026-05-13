from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Client, Service, Booking
from .selectors import client_has_active_booking
from .services import get_aware_datetime, has_booking_overlap


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
            "booking_date",
            "booking_time",
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
        booking_date = attrs["booking_date"]
        booking_time = attrs["booking_time"]
        telegram_id = attrs["telegram_id"]

        booking_datetime = get_aware_datetime(booking_date, booking_time)

        now = timezone.localtime()

        # Правило: запись минимум за 30 минут
        if booking_datetime < now + timedelta(minutes=30):
            raise serializers.ValidationError(
                "Запись можно создать минимум за 30 минут до начала."
            )

        # Правило: одна активная запись на пользователя
        if client_has_active_booking(telegram_id):
            raise serializers.ValidationError(
                "У пользователя уже есть активная запись."
            )

        # Проверка занятости слота
        if has_booking_overlap(booking_date, booking_time, service.duration):
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
