from datetime import datetime, timedelta
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
import os
import logging
import config
from handlers.common.constans import MAX_FILES_TO_SEND
from utils.data import get_all_orders_by_status, get_checklist_answers, mark_order_as_shown
from utils.file_handler import (
    get_user_files,
    get_files_by_stage_summary,
)
import traceback
from keyboards.inline import (
    get_orders_with_opened_keyboard,
)


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline import get_admin_order_keyboard
from utils.data import (
    get_order_by_id,
)
from utils.data import (
    get_progress_manager_ids,
    get_all_open_orders,
    get_open_orders_older_than,
    get_dealer_by_id,
    get_company_by_id,
    get_thread_information,
    get_thread_clients,
    get_open_orders_with_opened_at,
)
import asyncio

logger = logging.getLogger(__name__)


async def notify_admin_manager_assignment(bot, order, manager_id: int):
    """
    Уведомляет администратора о том, что менеджер взял заказ в работу
    
    Args:
        bot: Экземпляр бота для отправки сообщения
        order: Данные заказа
        manager_id: ID менеджера, который взял заказ
    """
    admin_id = config.get_admin_id()
    if not admin_id:
        return
    
    # Отправляем уведомление администратору
    await bot.send_message(
        admin_id,
        (
            "📌 <b>Заказ взят в работу</b>\n\n"
            f"🚗 <b>{order.get('brand','')} {order.get('model','')}</b>\n"
            f"🆔 Заказ: {order.get('id')}\n"
            f"👤 Осмотрщик: {manager_id}"
        ),
        parse_mode="HTML",
    )


async def notify_managers_order_opened(bot, order):
    """
    Уведомляет всех менеджеров о новом открытом заказе
    
    Отправляет уведомление всем авторизованным пользователям
    с кнопкой "Взять заказ". Исключает администратора и
    менеджеров, у которых уже есть заказы в работе.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
        order: Данные открытого заказа
    """
    try:
        admin_id = config.get_admin_id()
        allowed_users = config.get_allowed_users() or []
        # allowed_groups = config.get_allowed_groups() or []

        # Фильтруем только валидные ID пользователей
        allowed_users = [
            uid for uid in allowed_users if isinstance(uid, int) and uid > 100000
        ]

        # allowed_groups = [
        #     uid for uid in allowed_groups if isinstance(uid, int)
        # ]

        # Получаем ID менеджеров, у которых уже есть заказы в работе
        active_progress_ids = set(get_progress_manager_ids())
        
        # Формируем информацию о дилере
        dealer_text = ""
        dealer_id = order.get("dealers_id")

        if dealer_id:
            dealer = get_dealer_by_id(dealer_id)
            if dealer:
                parts = []
                if dealer.get("name"):
                    parts.append(dealer["name"])
                if dealer.get("phone"):
                    parts.append(str(dealer["phone"]))
                if dealer.get("address"):
                    parts.append(dealer["address"])
                if parts:
                    dealer_text = "\n<b>📍 Дилер:</b>\n" + "\n".join(parts)
        
        # Формируем текст уведомления
        text = (
            "🔔 <b>Открыт новый заказ</b>\n\n"
            f"🚗 <b>{order.get('brand','')} {order.get('model','')}</b>\n"
            f"🆔 Заказ: {order.get('id')}" + dealer_text + "\n\n"
            "Можно взять в работу — нажмите кнопку ниже."
        )
        
        # Создаем клавиатуру с кнопкой "Взять заказ"
        open_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 Взять заказ",
                        callback_data=f"order_status_{order.get('id')}",
                    )
                ]
            ]
        )
        
        # Отправляем уведомления всем подходящим пользователям
        for user_id in allowed_users:
            if not user_id:
                continue
            if user_id == admin_id:
                continue  # Пропускаем администратора
            if user_id in active_progress_ids:
                continue  # Пропускаем менеджеров с заказами в работе
            try:
                await bot.send_message(
                    user_id, text, parse_mode="HTML", reply_markup=open_kb
                )
                logger.info(f"notify_opened: sent to {user_id}")
            except Exception as e:
                logger.error(f"notify_opened: failed to send to {user_id}: {e}")
                continue


        # for user_id in allowed_groups:
        #     if not user_id:
        #         continue
        #     if user_id == admin_id:
        #         continue  # Пропускаем администратора
        #     if user_id in active_progress_ids:
        #         continue  # Пропускаем менеджеров с заказами в работе
        #     try:
        #         await bot.send_message(
        #             user_id, text, parse_mode="HTML", reply_markup=open_kb
        #         )
        #         logger.info(f"notify_opened: sent to {user_id}")
        #     except Exception as e:
        #         logger.error(f"notify_opened: failed to send to {user_id}: {e}")
        #         continue
    except Exception:
        # Логируем ошибки, но не прерываем работу
        pass


async def reminder_job(bot):
    try:
        open_orders = get_open_orders_older_than(60)
        # logger.info(f"open_orders: {open_orders}")
        if not open_orders:
            return

        for idx, order in enumerate(open_orders):
            if idx > 0:
                await asyncio.sleep(5)
            if order.get("shown_to_bot") == 1:  # или True, в зависимости от типа поля
                logger.info(f"reminder: order {order.get('id')} already shown, skipping")
                continue

            active_manager_ids = set(get_progress_manager_ids())
            admin_id = config.get_admin_id()
            allowed_users = set(
                [
                    uid
                    for uid in (config.get_allowed_users() or [])
                    if isinstance(uid, int) and uid > 100000
                ]
            )
            targets = [
                uid
                for uid in allowed_users
                if uid and uid != admin_id and uid not in active_manager_ids
            ]

            # allowed_groups = set(
            #     [
            #         uid
            #         for uid in (config.get_allowed_groups() or [])
            #         if isinstance(uid, int)
            #     ]
            # )
            # targets_groups = [
            #     uid
            #     for uid in allowed_groups
            # ]
            dealer_text = ""
            dealer_id = order.get("dealer_id")

            logger.info(f"open_orders: {dealer_id}")
            if dealer_id:
                dealer = get_dealer_by_id(dealer_id)
                logger.info(f"dealer: {dealer}")
                if dealer:
                    photo = dealer.get("photo")
                    parts = []
                    if dealer.get("name"):
                        if str(dealer["name"]).strip() not in ("", "0", None):
                            parts.append(str(dealer["name"]))

                    if dealer.get("company_name"):
                        if str(dealer["company_name"]).strip() not in ("", "0", None):
                            parts.append(str(dealer["company_name"]))

                    if dealer.get("phone"):
                        if str(dealer["phone"]).strip() not in ("", "0", None):
                            parts.append(str(dealer["phone"]))

                    if dealer.get("address"):
                        if str(dealer["address"]).strip() not in ("", "0", None):
                            parts.append(str(dealer["address"]))
                    if parts:
                        dealer_text = "\n<b>👨‍💻 Дилер:</b>\n"+ "" + "\n".join(parts)
                    
            company_id = order.get("company_id")
            logger.info(f"open_orders: {dealer_text}")
            if order.get("url"):
                link_text = f"\n<b>🔗Ссылка на авто:</b> {order['url']}"
            if company_id:
                company = get_company_by_id(company_id)
                if company:
                    parts = [f"\n<b>🏢 Компания:</b>"]
                    if company.get("name"):
                        parts.append(f"Наименование: {company['name']}")
                    if company.get("INN"):
                        parts.append(f"ИНН: {company['INN']}")
                    if company.get("OGRN"):
                        parts.append(f"ОГРН: {company['OGRN']}")
                    if company.get("address"):
                        parts.append(f"Адрес:{company['address']}")
                    if company.get("phone"):
                        parts.append(f"Телефон:{company['phone']}")
                    if company.get("email"):
                        parts.append(f"E-mail: {company['email']}")
                    company_text = "\n".join(parts)
            text = (
                "🔔 <b>Открытый заказ ожидает осмотрщика</b>\n\n"
                
                f"🚗 <b>{order.get('brand','')} {order.get('model','')} \n</b>({order.get('year','')}г., {order.get('mileage','')}км, {order.get('power','')} л.с.)\n"
                f"🆔 Заказ: {order.get('id')}\n" 
                f"📅 Создан: {order.get('opened_at')}\n" + link_text + '\n' + dealer_text + "\n" + company_text +

                "\nНажмите кнопку ниже, чтобы открыть заказ."
            )
            open_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📥 Взять заказ",
                            # callback_data=f"order_status_{order.get('id')}",
                            callback_data=f"order_time_{order.get('id')}",
                        )
                    ]
                ]
            )
            for uid in targets:
                try:
                    # if photo:
                    #     await bot.send_photo(
                    #     chat_id=uid,
                    #     photo=photo,
                    #     caption=text,
                    #     parse_mode="HTML",
                    #     reply_markup=open_kb,
                    # )
                    # else:
                    await bot.send_message(
                        uid, text, parse_mode="HTML", reply_markup=open_kb
                    )
                    logger.info(f"reminder: sent to {uid} for order {order.get('id')}")
                except Exception as e:
                    logger.error(
                        f"reminder: failed to send to {uid} for order {order.get('id')}: {e}"
                    )
                    continue

            # for uid in targets_groups:
            #     thread_id = get_thread_information(uid)
            #     try:
            #         await bot.send_message(
            #             uid, text, parse_mode="HTML", reply_markup=open_kb, message_thread_id=thread_id 
            #         )
            #         logger.info(f"reminder: sent to {uid} for order {order.get('id')}")
            #     except Exception as e:
            #         logger.error(
            #             f"reminder: failed to send to {uid} for order {order.get('id')}: {e}"
            #         )
            #         continue
            try:
                mark_order_as_shown(order.get("id"))
                logger.info(f"reminder: shown_to_bot set True for order {order.get('id')}")
            except Exception as e:
                logger.error(f"reminder: failed to update shown_to_bot for order {order.get('id')}: {e}")

                
    except Exception as e:
        logger.error(f"reminder_job top-level error: {e}\n{traceback.format_exc()}")

async def notify_manager_departure(bot, order_id: int, manager_id: int, arrival_time: datetime):
    try:
        arrival_time =  arrival_time + timedelta(hours=10)
        arrival_str = arrival_time.strftime("%Y-%m-%d %H:%M")
        text_manager = f"🚗 Менеджер <b>{manager_id}</b> отправился за заказом <b>{order_id}</b> и прибудет во <b>{arrival_str}</b>."
        # allowed_users = set(
        #     uid
        #     for uid in (config.get_allowed_users() or [])
        #     if isinstance(uid, int)
        # )

        allowed_groups = set(
            uid
            for uid in (config.get_allowed_groups() or [])
            if isinstance(uid, int)
        )

        # for uid in allowed_users:
        #     try:
        #         await bot.send_message(uid, text_manager, parse_mode="HTML")
        #         logger.info(f"reminder: sent manager info to {uid} for order {order_id}")
        #     except Exception as e:
        #         logger.error(f"reminder: failed to send manager info to {uid}: {e}")
        #         continue

        for uid in allowed_groups:
            message_thread = get_thread_clients(uid)
            try:
                await bot.send_message(uid, text_manager, parse_mode="HTML", message_thread_id=message_thread)
                logger.info(f"reminder: sent manager info to {uid} for order {order_id}")
            except Exception as e:
                logger.error(f"reminder: failed to send manager info to {uid}: {e}")
                continue

    except Exception as e:
        logger.error(f"notify_manager_departure error: {e}")


async def notify_manager_arrived(bot, order_id: int, manager_id: int):
    try:
        text_manager = f"📷 Осмотрщик <b>{manager_id}</b>, прикрепленный к заказу <b>{order_id}</b> прибыл на место и начал съемку авто."

        allowed_groups = set(
            uid
            for uid in (config.get_allowed_groups() or [])
            if isinstance(uid, int)
        )
        for uid in allowed_groups:
            message_thread = get_thread_clients(uid)
            try:
                await bot.send_message(uid, text_manager, parse_mode="HTML", message_thread_id=message_thread)
                logger.info(f"reminder: sent manager info to {uid} for order {order_id}")
            except Exception as e:
                logger.exception(f"Ошибка отправки уведомления в {uid}")
                continue

    except Exception as e:
        logger.exception(f"Ошибка отправки уведомления в {uid}")



async def reminder_open_bids(bot):
    try:
        open_orders = get_open_orders_older_than(60)
        count = len(open_orders)
        if not open_orders:
            return

        text = (
            f"🔔 Внимание! Есть открытые заявки.\n"
            f"Количество открытых заявок на сегодня: <b> {count} </b>"
        )
        active_manager_ids = set(get_progress_manager_ids())
        admin_id = config.get_admin_id()
        allowed_users = set(
            uid
            for uid in (config.get_allowed_users() or [])
            if isinstance(uid, int)
        )
        targets = [
            uid
            for uid in allowed_users
            if uid and uid != admin_id and uid not in active_manager_ids
        ]

        # allowed_groups = set(
        #     uid
        #     for uid in (config.get_allowed_groups() or [])
        #     if isinstance(uid, int)
        # )
        # targets_groups = [
        #     uid
        #     for uid in allowed_groups
        # ]
        orders = get_open_orders_with_opened_at()

        for uid in targets:
            try:
                await bot.send_message(uid, text, parse_mode="HTML", reply_markup=get_orders_with_opened_keyboard(orders))
                logger.info(f"reminder: sent to {uid} about open bids")
            except Exception as e:
                logger.error(f"reminder: failed to send to {uid}: {e}")
                continue


        # for uid in targets_groups:
        #     thread_id = get_thread_information(uid)
        #     try:
        #         await bot.send_message(uid, text, parse_mode="HTML", message_thread_id=thread_id, reply_markup=get_orders_with_opened_keyboard(orders))
        #         logger.info(f"reminder: sent to {uid} about open bids")
        #     except Exception as e:
        #         logger.error(f"reminder: failed to send to {uid}: {e}")
        #         continue
    except Exception as e:
        logger.error(f"reminder_open_bids error: {e}")


async def notify_admin_manager_decline(bot, order, manager_id: int, reason: str):
    admin_id = config.get_admin_id()
    if not admin_id:
        return
    await bot.send_message(
        admin_id,
        (
            "⚠️ <b>Осмотрщик отказался от заказа</b>\n\n"
            f"🚗 <b>{order.get('brand','')} {order.get('model','')}</b>\n"
            f"🆔 Заказ: {order.get('id')}\n"
            f"👤 Осмотрщик: {manager_id}\n"
            f"📝 Причина: {reason or 'не указана'}"
        ),
        parse_mode="HTML",
    )


async def send_files_to_admin(
    order_id: str, photographer_user_id: int, bot, is_rework: bool = False
):
    try:
        
        admin_id = config.get_admin_id()
        if admin_id is None:
            logger.error("Админ не найден")
            return
        allowed_groups = set(
            uid
            for uid in (config.get_allowed_groups() or [])
            if isinstance(uid, int)
        )
        targets_groups = [
            uid
            for uid in allowed_groups
        ]
        order = get_order_by_id(order_id)
        files = get_user_files(photographer_user_id, order_id)
        if is_rework:

            def is_additional_file(f):
                stage_ok = f.get("stage") == "📷 Дополнительные материалы"
                name = os.path.basename(f.get("path", ""))
                prefix_ok = name.startswith(
                    "Дополнительные_материалы_"
                ) or name.startswith("📷_Дополнительные_материалы_")
                return stage_ok or prefix_ok

            files = [f for f in files if is_additional_file(f)]

        checklist = get_checklist_answers(order_id)

        prefix = (
            "🔄 <b>Заказ после доработки!</b>"
            if is_rework
            else "🆕 <b>Новый заказ на проверку!</b>"
        )
        header_text = (
            f"{prefix}\n\n"
            f"<b>{order.get('brand', '')} {order.get('model', '')}</b>\n"
            f"\n👤 Фотограф ID: {photographer_user_id}\n"
            f"📁 Всего файлов: {len(files)}"
        )
        await bot.send_message(admin_id, header_text, parse_mode="HTML")

        photos = [f for f in files if f.get("type") == "photo"]
        if photos:
            media_group = [
                InputMediaPhoto(media=FSInputFile(f["path"]))
                for f in photos[:MAX_FILES_TO_SEND]
            ]
            if media_group:
                await bot.send_media_group(admin_id, media_group)

        for f in [f for f in files if f.get("type") == "video"]:
            await bot.send_video(admin_id, FSInputFile(f["path"]))

        cp1 = checklist.get("checklist_point1") if isinstance(checklist, dict) else None
        cp2 = checklist.get("checklist_point2") if isinstance(checklist, dict) else None

        def _fmt(val):
            if val is None or str(val).strip() == "":
                return "не указано"
            return str(val)

        q1_label = "Состояние бампера"
        q2_label = "Уровень топлива в баке"
        checklist_text = (
            "📋 <b>Чеклист:</b>\n"
            f"{q1_label}: {_fmt(cp1)}\n"
            f"{q2_label}: {_fmt(cp2)}\n"
        )
        await bot.send_message(admin_id, checklist_text, parse_mode="HTML")

        kb = get_admin_order_keyboard(str(order_id))
        action_text = (
            "Заказ после доработки - выберите действие:"
            if is_rework
            else "Выберите действие после проверки:"
        )
        await bot.send_message(admin_id, action_text, reply_markup=kb)

        prefix_group = (
            "🔄 <b>Информация по новому заказу после доработки!</b>"
            if is_rework
            else "🆕 <b>Информация по новому заказу!</b>"
        )
        header_text1 = (
            f"{prefix_group}\n\n"
            f"<b>{order.get('brand', '')} {order.get('model', '')}</b>\n"
            f"\n👤 Фотограф ID: {photographer_user_id}\n"
            f"📁 Всего файлов: {len(files)}"
        )
        for uid in targets_groups:
            thread_id = get_thread_information(uid)
            try:
                await bot.send_message(uid, header_text1, parse_mode="HTML", message_thread_id=thread_id)
                await bot.send_media_group(uid, media_group, message_thread_id=thread_id)
                await bot.send_video(uid, FSInputFile(f["path"]), message_thread_id=thread_id)
                await bot.send_message(uid, checklist_text, parse_mode="HTML", message_thread_id=thread_id)
                logger.info(f"reminder: sent to {uid} about open bids")
            except Exception as e:
                logger.error(f"reminder: failed to send to {uid}: {e}")
                continue
    except Exception as e:
        logger.error(f"Ошибка отправки заказа админу: {e}")


async def send_pending_orders_to_new_admin(bot, admin_id: int):
    try:
        review_orders = get_all_orders_by_status(["review"])

        if not review_orders:
            await bot.send_message(admin_id, "📋 Нет заказов, ожидающих проверки.")
            return

        await bot.send_message(
            admin_id,
            f"📋 <b>Найдено {len(review_orders)} заказов на проверке</b>\n"
            f"Отправляю все заявки...",
            parse_mode="HTML",
        )

        for order in review_orders:
            try:
                manager_id = order.get("manager_id")
                if manager_id:
                    await send_files_to_admin(
                        order["id"], manager_id, bot, is_rework=False
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке заказа {order.get('id')}: {e}")

        await bot.send_message(admin_id, "✅ Все заявки отправлены!")

    except Exception as e:
        logger.error(f"Ошибка при отправке заявок: {e}")
        await bot.send_message(admin_id, "❌ Произошла ошибка при отправке заявок.")
