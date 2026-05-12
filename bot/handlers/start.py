from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main_menu import main_keyboard


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Здравствуйте! Я бот для записи в барбершоп 💈\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard
    )