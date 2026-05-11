from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Записаться"),
        ],
        [
            KeyboardButton(text="Моя запись"),
            KeyboardButton(text="Отменить запись"),
        ],
    ],
    resize_keyboard=True
)
