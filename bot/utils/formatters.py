def format_booking(booking: dict) -> str:
    service = booking.get("service", {})
    client = booking.get("client", {})

    booking_id = booking.get("id")
    date = booking.get("booking_date") or booking.get("date") or "Не указано"
    time = booking.get("booking_time") or booking.get("time") or "Не указано"
    status = booking.get("status")

    service_name = service.get("name", "Не указано")
    service_price = service.get("price", "Не указано")
    service_duration = service.get("duration", "Не указано")

    client_name = client.get("name", "Не указано")
    client_phone = client.get("phone", "Не указано")

    status_text = {
        "pending": "Ожидает подтверждения",
        "confirmed": "Подтверждена",
        "cancelled": "Отменена",
        "completed": "Завершена",
    }.get(status, status)

    return (
        "📌 <b>Ваша активная запись</b>\n\n"
        f"🆔 <b>ID записи:</b> {booking_id}\n"
        f"📅 <b>Дата:</b> {date}\n"
        f"⏰ <b>Время:</b> {time}\n"
        f"📍 <b>Статус:</b> {status_text}\n\n"
        f"💈 <b>Услуга:</b> {service_name}\n"
        f"💰 <b>Цена:</b> {service_price} ₸\n"
        f"⏳ <b>Длительность:</b> {service_duration}\n\n"
        f"👤 <b>Клиент:</b> {client_name}\n"
        f"📞 <b>Телефон:</b> {client_phone}"
    )
