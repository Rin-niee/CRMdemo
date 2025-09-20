
import os
import config
# from utils.data import mark_order_as_shown
import traceback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.data import (
    get_company_by_id,
    get_rings_orders,
    get_thread_calls,
    mark_order_as_shown_to_caller,
    get_all_order
)
from keyboards.main_kb import build_orders_keyboard
import logging
import asyncio
logger = logging.getLogger(__name__)

async def reminder_job(bot):
    try:
        orders = await get_all_order()
        rings_orders = await get_rings_orders()
        if not rings_orders:
            return
        # logger.info(rings_orders)
        for idx, order in enumerate(rings_orders):
            if idx > 0:
                await asyncio.sleep(5)
            if order.get("caller_saw") == 1:
                logger.info(f"reminder: order {order.get('id')} already shown, skipping")
                continue

            allowed_groups = set(
                [
                    uid
                    for uid in (await config.get_caller_id() or [])
                    if isinstance(uid, int)
                ]
            )
            logger.info(f"LALALALA {allowed_groups}")
            targets = [
                uid
                for uid in allowed_groups
                if uid
            ]
            
            company_id = order.get("company_id")
            if order.get("url_users"):
                link_text = f"\n<b>🔗Ссылка на авто:</b> {order['url_users']}"
            
            if company_id:
                company = await get_company_by_id(company_id)
                company_text=[]
                company_text.append(
                    "\n🏢<b> Компания: </b>\n" +
                    "Наименование: " + (company.get("name") or "Неизвестно") +
                    "\nИНН: " + (company.get("INN") or "Неизвестно") +
                    "\nАдрес: " + (company.get("OGRN") or "Неизвестно") +
                    "\nТелефон: " + (company.get("phone") or "Неизвестно") +
                    "\nE-mail: " + (company.get("email") or "Неизвестно")
                )
            else:
                company_text = ""
            text = (
                "🔔 <b>Открыта новая заявка</b>\n\n" +
                f"🆔 Заявка: {order.get('id')}\n" +
                    link_text + '\n' + company_text
            )
            for uid in targets:
                try:
                    thread_id = await get_thread_calls(uid)
                    logger.info(orders)
                    await bot.send_message(
                        uid, text, parse_mode="HTML", message_thread_id=thread_id, reply_markup = await build_orders_keyboard([orders])
                    )
                    logger.info(f"reminder: sent to {uid} for order {order.get('id')}")
                except Exception as e:
                    logger.error(
                        f"reminder: failed to send to {uid} for order {order.get('id')}: {e}"
                    )
                    continue
            try:
                await mark_order_as_shown_to_caller(order.get("id"))
                logger.info(f"reminder: shown_to_bot set True for order {order.get('id')}")
            except Exception as e:
                logger.error(f"reminder: failed to update shown_to_bot for order {order.get('id')}: {e}")

                
    except Exception as e:
        logger.error(f"reminder_job top-level error: {e}\n{traceback.format_exc()}")


async def reminder_open_bids(bot):
    try:
        open_orders = await get_rings_orders()
        count = len(open_orders)
        if not open_orders:
            return

        text = (
            f"🔔 Внимание! Есть открытые заявки.\n"
            f"Количество открытых заявок на сегодня: <b> {count} </b>"
        )
        await config.load_roles_from_db()

        allowed_users = set(
            uid
            for uid in (await config.get_caller_id() or [])
            if isinstance(uid, int)
        )
        logger.info(f"LALALALA {allowed_users}")
        targets = [
            uid
            for uid in allowed_users
            if uid
        ]
        
        kb = await build_orders_keyboard(open_orders)
        for uid in targets:
            try:
                await bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)
                logger.info(f"reminder: sent to {uid} about open bids")
            except Exception as e:
                logger.error(f"reminder: failed to send to {uid}: {e}")
                continue

    except Exception as e:
        logger.error(f"reminder_open_bids error: {e}")
