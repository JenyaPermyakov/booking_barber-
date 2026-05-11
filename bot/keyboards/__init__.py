from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.booking import BookingState


router = Router()


@router.message(F.text == "Записаться")
async def start_booking(message: Message, state: FSMContext):
    await state.set_state(BookingState.choosing_service)

    await message.answer(
        "Отлично, начинаем запись.\n\n"
        "Следующий шаг — выбрать услугу."
    )