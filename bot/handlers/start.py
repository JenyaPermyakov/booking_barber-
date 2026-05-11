from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu_keyboard


router = Router()


@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        text=(
            "Здравствуйте 👋\n\n"
            "Я бот для записи на стрижку.\n"
            "Выберите действие в меню ниже:"
        ),
        reply_markup=main_menu_keyboard,
    )