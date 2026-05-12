from aiogram import Router, F
from aiogram.types import Message

from bot.services.api import get_my_booking
from bot.utils.formatters import format_booking

router = Router()


@router.message(F.text == "Моя запись")
async def my_booking_handler(message: Message):
    telegram_id = message.from_user.id

    booking = await get_my_booking(telegram_id)

    if not booking:
        await message.answer(
            "У вас нет активной записи 📭"
        )
        return

    await message.answer(
        format_booking(booking),
        parse_mode="HTML"
    )