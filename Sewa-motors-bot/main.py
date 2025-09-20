import asyncio
from datetime import datetime
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram import types, Router
import config
from handlers.auth.middleware import AuthMiddleware
from handlers.commands import basic, admin, orders as orders_commands
from handlers.navigation import menu, filters
from handlers.orderss import selection, photo_session, status, rework, review, checklist, precheck
import re
from config import BOT_TOKEN
from handlers import files
from crm_integration import create_bid_in_crm, wait_for_bid_details, update_bid_topics
from config import BOT_TOKEN
from utils.data import get_bid_by_thread_id,get_bid_info
import requests
CRM_URL = "http://web:8000/api/message/create/"
from config import CRM_TOKEN


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
orders_router = Router()
bot = Bot(token=BOT_TOKEN)
local_folder = "storage/TGphoto"
os.makedirs(local_folder, exist_ok=True)

# Обработчик для сообщений и создания заявки
@orders_router.message(lambda message: message.text and "#заявка" in message.text)
async def test_all_messages(message: types.Message):
    match = re.search(r"https?://\S+", message.text)
    if match:
        url = match.group(0)
        created_bid = create_bid_in_crm(
            url_users=url
        )
    if created_bid:
        bid_instance = await wait_for_bid_details(created_bid.get("id"))
        name = f"{bid_instance.get('brand', '')} {bid_instance.get('model', '')} {bid_instance.get('year', '')}"
        last_topic = None
        allowed_groups = set(
            uid
            for uid in (await config.get_allowed_groups() or [])
            if isinstance(uid, int)
        )
        for chat_id in allowed_groups:
            try:
                last_topic = await bot.create_forum_topic(chat_id=chat_id, name=name)
                await message.reply(f"Заявка получена! Тема успешно создана в группе {chat_id}! Тема ID: {last_topic.message_thread_id}")
                try:
                    await update_bid_topics(created_bid.get("id"), last_topic.message_thread_id)
                except Exception as e:
                    logger.error(f"Проблема тут {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Не удалось создать тему в группе {chat_id}: {e}")
            

        if last_topic is None:
            await message.reply(f"Не удалось создать тему ни в одной группе.")

    else:
        await message.reply("Не могу найти ссылку в сообщении.")


# Обработчик для сообщений и сохранение их в бд для дальнейшей отправки в CRM
@orders_router.message(lambda message: getattr(message, 'message_thread_id', None) is not None)
async def log_message(message: types.Message):
    bid_row = await get_bid_by_thread_id(message.message_thread_id)
    if not bid_row:
        return
    bid_info_list = await get_bid_info(bid_row['id'])
    if not bid_info_list:
        return

    bid_info = bid_info_list[0]
    topic_name = f"{bid_info['brand']} {bid_info['model']} {bid_info['year']}"
    payload = {
        "bid": bid_row['id'],
        "chat_id": message.chat.id,
        "message_thread_id": message.message_thread_id,
        "message_id": message.message_id,
        "user_id": message.from_user.id,
        "username": message.from_user.username or "",
        "topic_name":topic_name,
        "text": message.text,
        "media": [],
        "created_at" : datetime.utcnow().isoformat() 
    }

    if getattr(message, "photo", None):
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        filename = os.path.basename(file_info.file_path)
        local_path = os.path.join(local_folder, filename)
        url = f"/media/TGphoto/{filename}"
        await bot.download_file(file_info.file_path, local_path)
        payload["media"].append({
            "type": "photo",
            "file_url": url,
        })

    if getattr(message, "video", None):
        file_info = await bot.get_file(message.video.file_id)
        filename = os.path.basename(file_info.file_path)
        local_path = os.path.join(local_folder, filename)
        url = f"/media/TGphoto/{filename}"
        await bot.download_file(file_info.file_path, local_path)
        payload["media"].append({
            "type": "video",
            "file_url": url,
        })
    try:
        requests.post(CRM_URL, json=payload, headers={"Authorization": f"Token {CRM_TOKEN}"}, timeout=5)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в CRM: {e}")

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
    await config.load_roles_from_db()

    # Создаем диспетчер с хранилищем состояний в памяти
    dp = Dispatcher(storage=MemoryStorage())
    #сбор заявок
    dp.include_router(orders_router)
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
    
    # Удаляем webhook и настраиваем команды бота
    await bot.delete_webhook(drop_pending_updates=True)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="myorders", description=f"Мои заявки"),
            BotCommand(command="orderplan", description="Открытые заявки"),
            BotCommand(command="chatid", description="Узнать ID чата"),
        ]
    )

    try:
        # Импортируем функцию для отправки напоминаний
        from handlers.admin.notifications import reminder_open_bids, reminder_job 
        async def reminders_loop():
            """
            Бесконечный цикл для отправки напоминаний
            Проверяет заказы каждую минуту и отправляет уведомления
            """
            timer = 0
            while True:
                try:
                    await reminder_job(bot)
                    if timer >= 50:
                        logger.info("15 минут прошли — запускаем reminder_open_bids")
                        await reminder_open_bids(bot)
                        timer = 0 
                    else:
                        logger.info(f"Таймер: {timer} секунд")
                except Exception:
                    pass
                await asyncio.sleep(10)
                timer +=10

        # Запускаем фоновую задачу для напоминаний
        asyncio.create_task(reminders_loop())

        # Запускаем бота в режиме polling (опрос сервера Telegram)
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
