from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=150, verbose_name='Имя клиента')
    phone = models.CharField(max_length=11, verbose_name='Телефон')
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name='Telegram ID')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название услуги')
    price = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена')
    duration = models.DurationField(verbose_name='Длительность')
    is_active = models.BooleanField(default=True,verbose_name='Активна')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает подтверждения"
        CONFIRMED = "confirmed", "Подтверждена"
        CANCELLED = "cancelled", "Отменена"
        COMPLETED = "completed", "Завершена"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент', related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name='Услуга', related_name='bookings')

    booking_date = models.DateField(verbose_name='Дата записи')
    booking_time = models.TimeField(verbose_name='Время записи')
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING, verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return f'{self.booking_date} - {self.booking_time}'
