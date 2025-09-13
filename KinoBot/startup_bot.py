from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio, config, database, subCheck_logic

from ReplyKbLogic import router as ReplyKbRouter
from SearchFilmLogic import router as searchFilmRouter
from showLikedLogic import router as showLikedRouter

async def start_userbot():
    await subCheck_logic.userbot.connect()
    if not await subCheck_logic.userbot.is_user_authorized():
        print("⚠️ Userbot не авторизован. Введите номер телефона и код вручную:")   
        await subCheck_logic.userbot.start()  # запросит код, если сессии нет
    print("✅ Userbot успешно запущен!")

async def main():
    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    await database.init_pools()

    dp.include_router(ReplyKbRouter)
    dp.include_router(showLikedRouter)
    dp.include_router(searchFilmRouter)

    try:
        await start_userbot()
        print("✅ Userbot успешно подключён!")
    except Exception as e:
        print(f"❌ Ошибка запуска userbot: {e}")

    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())