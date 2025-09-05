import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import menu
from handlers.menu import router
import logging
from handlers.notifications import reminder_job, reminder_open_bids

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(menu.router)
logging.basicConfig(level=logging.INFO)  # INFO или DEBUG
logger = logging.getLogger(__name__)
async def main():
    try:
        async def reminders_loop():
            """
            Бесконечный цикл для отправки напоминаний
            Проверяет заказы каждую минуту и отправляет уведомления
            """
            timer = 0
            while True:
                try:
                    await reminder_job(bot)
                    if timer >= 20:
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
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

