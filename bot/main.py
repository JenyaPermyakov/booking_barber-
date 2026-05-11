import asyncio

from aiogram import Bot, Dispatcher

from bot.config.settings import BOT_TOKEN
from bot.handlers.start import router as start_router
from bot.handlers.booking import router as booking_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(booking_router)

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())