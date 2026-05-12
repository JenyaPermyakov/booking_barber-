import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.booking import router as booking_router
from bot.handlers.my_booking import router as my_booking_router
from bot.handlers.cancel_booking import router as cancel_booking_router
from bot.handlers.change_booking import router as change_booking_router


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "backend" / ".env"

load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл backend/.env")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(my_booking_router)
    dp.include_router(cancel_booking_router)
    dp.include_router(change_booking_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())