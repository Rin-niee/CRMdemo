import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram import types, Router
import config
from handlers.auth.middleware import AuthMiddleware
from handlers.commands import basic, admin, orders as orders_commands
from handlers.navigation import menu, filters
from handlers.orderss import selection, photo_session, status, rework, review, checklist, precheck

from config import BOT_TOKEN
from handlers import files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# debug_router = Router()

# @debug_router.message()
# async def echo_chat_id(message: types.Message):
#     print(f"[DEBUG] chat_id = {message.chat.id}")
#     await message.answer(f"chat_id этого чата: {message.chat.id}")

# router = Router()
# @router.message()
# async def get_thread_id(message: types.Message):
#     if message.message_thread_id:
#         await message.answer(f"ID этой темы: {message.message_thread_id}")
#     else:
#         await message.answer("Это сообщение не из темы.")

async def main():
    """
    Главная функция запуска Telegram бота
    Инициализирует бота, настраивает middleware и роутеры
    """
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не задан")
        return

    # Создаем экземпляр бота
    bot = Bot(token=BOT_TOKEN)
    
    # Загружаем роли пользователей из базы данных
    config.load_roles_from_db()

    # Создаем диспетчер с хранилищем состояний в памяти
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем middleware для авторизации пользователей
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Подключаем все роутеры для обработки различных команд и действий
    
    # Роутеры для работы с заказами
    dp.include_router(selection.router)        # Выбор и просмотр заказов
    dp.include_router(precheck.router)         # Предварительная проверка авто
    dp.include_router(photo_session.router)    # Фотосессия автомобиля
    dp.include_router(checklist.router)        # Чек-лист проверки

    # Роутеры для навигации и управления
    dp.include_router(filters.router)          # Фильтры по статусу заказов
    dp.include_router(status.router)           # Управление статусами
    dp.include_router(rework.router)           # Переделка заказов
    dp.include_router(review.router)           # Просмотр и проверка
    dp.include_router(menu.router)             # Главное меню
    dp.include_router(orders_commands.router)  # Команды для работы с заказами
    dp.include_router(basic.router)            # Базовые команды (start, help)
    dp.include_router(admin.router)            # Административные команды

    # Роутер для работы с файлами
    dp.include_router(files.router)
    #МОЙ
    # dp.include_router(debug_router)
    dp.include_router(router)
    # Удаляем webhook и настраиваем команды бота
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="myorders", description="Мои заказы"),
            BotCommand(command="orderplan", description="Заказы на сегодня"),
            BotCommand(command="openorders", description="Открыть заказы"),
        ]
    )

    try:
        # Импортируем функцию для отправки напоминаний
        from handlers.admin.notifications import reminder_open_bids, reminder_job 
        # await reminder_job(bot)
        async def reminders_loop():
            """
            Бесконечный цикл для отправки напоминаний
            Проверяет заказы каждую минуту и отправляет уведомления
            """
            while True:
                try:
                    await reminder_job(bot)
                    await reminder_open_bids(bot)
                except Exception:
                    pass
                await asyncio.sleep(900)

        # Запускаем фоновую задачу для напоминаний
        asyncio.create_task(reminders_loop())

        # Запускаем бота в режиме polling (опрос сервера Telegram)
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
