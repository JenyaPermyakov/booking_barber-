from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards.booking import get_services_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.api import delete_booking, get_client_by_telegram_id, get_my_booking, get_services
from bot.states.booking import BookingState
from bot.utils.formatters import format_booking

router = Router()


def get_change_booking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Начать изменение",
                    callback_data="change_booking_start",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Оставить как есть",
                    callback_data="change_booking_keep",
                )
            ],
        ]
    )


@router.message(F.text == "Изменить запись")
async def change_booking_handler(message: Message):
    telegram_id = message.from_user.id

    booking = await get_my_booking(telegram_id)

    if not booking:
        await message.answer(
            "У вас нет активной записи для изменения 📭\n\n"
            "Нажмите «Записаться», чтобы создать новую запись."
        )
        return

    await message.answer(
        f"{format_booking(booking)}\n\n"
        "Чтобы изменить запись, текущая запись будет отменена, "
        "после этого вы выберете новую услугу, дату и время.",
        parse_mode="HTML",
        reply_markup=get_change_booking_keyboard(),
    )


@router.callback_query(F.data == "change_booking_keep")
async def keep_booking_handler(callback: CallbackQuery):
    await callback.message.answer(
        "Хорошо, оставляем текущую запись без изменений.",
        reply_markup=main_menu_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "change_booking_start")
async def start_change_booking_handler(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    booking = await get_my_booking(telegram_id)

    if not booking:
        await callback.message.answer(
            "Активная запись не найдена. Можно создать новую запись.",
            reply_markup=main_menu_keyboard,
        )
        await callback.answer()
        return

    booking_id = booking.get("id")

    if not booking_id:
        await callback.message.answer(
            "Не удалось определить ID записи.",
            reply_markup=main_menu_keyboard,
        )
        await callback.answer()
        return

    services = await get_services()

    if not services:
        await callback.message.answer(
            "Сейчас список услуг недоступен. Попробуйте позже.",
            reply_markup=main_menu_keyboard,
        )
        await callback.answer()
        return

    client = booking.get("client") or await get_client_by_telegram_id(telegram_id)
    is_deleted = await delete_booking(booking_id)

    if not is_deleted:
        await callback.message.answer(
            "❌ Не удалось отменить текущую запись.\n"
            "Возможно, изменение доступно минимум за 2 часа до записи.",
            reply_markup=main_menu_keyboard,
        )
        await callback.answer()
        return

    await state.clear()
    await state.update_data(telegram_id=telegram_id)

    if client:
        await state.update_data(
            name=client.get("name"),
            phone=client.get("phone"),
        )

    await state.set_state(BookingState.choosing_service)

    await callback.message.answer(
        "Текущая запись отменена ✅\n\n"
        "Выберите новую услугу:",
        reply_markup=get_services_keyboard(services),
    )
    await callback.answer()
