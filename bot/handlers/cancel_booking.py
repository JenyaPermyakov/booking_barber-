from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.api import get_my_booking, delete_booking

router = Router()


@router.message(F.text == "Отменить запись")
async def cancel_booking_handler(message: Message):
    telegram_id = message.from_user.id

    booking = await get_my_booking(telegram_id)

    if not booking:
        await message.answer(
            "У вас нет активной записи для отмены 📭"
        )
        return

    booking_id = booking.get("id")

    if not booking_id:
        await message.answer(
            "Не удалось определить ID записи."
        )
        return

    is_deleted = await delete_booking(booking_id)

    if is_deleted:
        await message.answer(
            "✅ Ваша запись успешно отменена.",
            reply_markup=main_menu_keyboard,
        )
    else:
        await message.answer(
            "❌ Не удалось отменить запись.\n"
            "Возможно, отмена доступна минимум за 2 часа до записи."
        )
