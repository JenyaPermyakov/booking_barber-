from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_services_keyboard(services: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []

    for service in services:
        service_id = service["id"]
        name = service["name"]
        price = service["price"]

        keyboard.append([
            InlineKeyboardButton(
                text=f"{name} — {price} ₸",
                callback_data=f"service_{service_id}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_dates_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    today = date.today()

    for day_number in range(7):
        current_date = today + timedelta(days=day_number)

        keyboard.append([
            InlineKeyboardButton(
                text=current_date.strftime("%d.%m.%Y"),
                callback_data=f"date_{current_date.isoformat()}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_slots_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []

    for slot in slots:
        time = slot["time"]

        keyboard.append([
            InlineKeyboardButton(
                text=time,
                callback_data=f"time_{time}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить запись",
                    callback_data="confirm_booking",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_booking_process",
                )
            ],
        ]
    )