from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.admin.notifications import (
    send_files_to_admin,
    notify_admin_manager_decline,
)
from utils.file_handler import (
    get_user_files,
)
import logging
from utils.data import (
    update_order_status, 
    get_checklist_answers,
    get_dealer_by_id,
    get_thread_information, 
    get_order_by_id,
)

from handlers.common.constans import MAX_FILES_TO_SEND
router = Router()
logger = logging.getLogger(__name__)


async def is_admin(user_id: int) -> bool:
    return await config.is_admin(user_id)


class AdminReworkStates(StatesGroup):
    waiting_task_text = State()
    waiting_decline_reason = State()


@router.callback_query(F.data.startswith("admin_rework_with_task_"))
async def admin_rework_with_task_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может отправлять заказы на доработку!",
            show_alert=True,
        )
        return
    order_id = int(callback.data[len("admin_rework_with_task_") :])
    await state.update_data(rework_order_id=order_id)
    await state.set_state(AdminReworkStates.waiting_task_text)
    await callback.message.answer(
        "📝 Введите текст дополнительного задания для осмотрщика одним сообщением."
    )
    await callback.answer()


@router.message(AdminReworkStates.waiting_task_text, F.text)
async def capture_admin_task_text(message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("rework_order_id")
    if not await is_admin(message.from_user.id):
        return
    task_text = message.text or ""
    order = await get_checklist_answers(order_id)
    if not order:
        await message.answer("Заказ не найден!")
        await state.clear()
        return
    photographer_id = order.get("manager_id")
    if not photographer_id:
        await message.answer("Осмотрщик для этого заказа не назначен!")
        await state.clear()
        return

    await update_order_status(order_id, "progress")
    rework_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📷 Перейти к доработке",
                    callback_data=f"continue_order_{order_id}",
                )
            ]
        ]
    )

    dealer_block = ""
    dealer_id = order.get("dealers_id")
    if dealer_id:
        dealer = await get_dealer_by_id(dealer_id)
        if dealer:
            parts = []
            if dealer.get("name"):
                parts.append(dealer["name"])
            if dealer.get("phone"):
                parts.append(str(dealer["phone"]))
            if dealer.get("address"):
                parts.append(dealer["address"])
            if parts:
                dealer_block = "<b>📍 Дилер:</b>\n" + "\n".join(parts)

    lines = [
        "🔄 <b>Доработка заказа</b>",
        "",
        f"🚗 <b>{order.get('brand','')} {order.get('model','')}</b>",
    ]
    if dealer_block:
        lines.append(dealer_block)
    lines.extend(["", "<b>Задание от администратора:</b>", task_text])
    text = "\n".join(lines)

    await message.bot.send_message(
        photographer_id,
        text,
        reply_markup=rework_kb,
        parse_mode="HTML",
    )
    await message.answer(
        "✅ Задание отправлено осмотрщику и заказ переведён в доработку."
    )
    await state.clear()


@router.callback_query(F.data.startswith("finish_additional_"))
async def finish_additional_task(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("finish_additional_") :]
    user_id = callback.from_user.id

    await send_files_to_admin(order_id, user_id, callback.bot, is_rework=True)
    await update_order_status(order_id, "review")

    await callback.answer(
        "Доп. задача завершена, материалы отправлены админу.", show_alert=True
    )
    await callback.message.edit_text("✅ Дополнительная задача завершена.")


@router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_order(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может подтверждать заказы!", show_alert=True
        )
        return
    photographer_user_id = int(callback.from_user.id)
    logger.info(f"ПОЛЬЗОВАТЕЛЬ: {photographer_user_id}")
    order_id = callback.data[14:]
    order = await get_order_by_id(int(order_id))
    logger.info(f"ID: {order_id}")
    manager_id = order.get("manager_id") if order else None

    await update_order_status(int(order_id), "done")

    await callback.answer(
        "✅ Заказ подтверждён! Статус изменён на 'Выполнен'.", show_alert=True
    )
    await callback.message.edit_text(
        "✅ <b>Заказ подтверждён и завершён.</b>", parse_mode="HTML"
    )
    allowed_groups = set(
        uid
        for uid in (await config.get_allowed_groups() or [])
        if isinstance(uid, int)
    )
    targets_groups = [
            uid
            for uid in allowed_groups
        ]
    


    files = get_user_files(photographer_user_id, str(order_id))
    logger.info("fФАЙЛЫ ЕСТЬ ИЛИ НЕТ: {files}")
    checklist = await get_checklist_answers(int(order_id))

    header_text = (
        f"<b>{order.get('brand', '')} {order.get('model', '')}</b>\n"
        f"\n👤 Фотограф ID: {photographer_user_id}\n"
        f"📁 Всего файлов: {len(files)}"
    )

    photos = [f for f in files if f.get("type") == "photo"]

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
    for uid in targets_groups:
        thread_id = await get_thread_information(uid)
        try:
            await callback.bot.send_message(uid, header_text, parse_mode="HTML", message_thread_id=thread_id)
            if photos:
                media_group = [
                    InputMediaPhoto(media=FSInputFile(f["path"]))
                    for f in photos[:MAX_FILES_TO_SEND]
                ]
                if media_group:
                    await callback.bot.send_media_group(uid, media_group, message_thread_id=thread_id)

            for f in [f for f in files if f.get("type") == "video"]:
                await callback.bot.send_video(uid, FSInputFile(f["path"]), message_thread_id=thread_id)
            await callback.bot.send_message(uid, checklist_text, parse_mode="HTML", message_thread_id=thread_id)
            logger.info(f"reminder: sent to {uid} about open bids")
        except Exception as e:
            logger.error(f"reminder: failed to send to {uid}: {e}")
            continue
    if manager_id:
        try:
            car = f"{(order or {}).get('brand','')} {(order or {}).get('model','')}".strip()
            text = (
                "✅ <b>Заказ завершён</b>\n\n"
                f"🚗 <b>{car}</b>\n"
                f"🆔 Заказ: {order_id}\n\n"
                "Статус: Выполнен. Спасибо за работу!"
            )
            await callback.bot.send_message(manager_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось уведомить осмотрщика о завершении заказа {order_id}: {e}")


@router.callback_query(F.data.startswith("admin_rework_"))
async def admin_rework_order(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может отправлять заказы на доработку!",
            show_alert=True,
        )
        return

    order_id = callback.data[13:]
    order = await get_checklist_answers(order_id)

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    await update_order_status(order_id, "progress")

    photographer_id = order.get("manager_id")
    if photographer_id:
        try:
            rework_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📷 Добавить дополнительные фото",
                            callback_data=f"continue_order_{order_id}",
                        )
                    ]
                ]
            )

            await callback.bot.send_message(
                photographer_id,
                f"🔄 <b>Заказ отправлен на доработку</b>\n\n"
                f"🚗 <b>{order.get('brand', '')} {order.get('model', '')}</b>\n"
                f"📋 {order.get('title', '')}\n\n"
                f"Администратор запросил дополнительные материалы для этого заказа. "
                f"Вы можете добавить дополнительные фотографии или видео.",
                reply_markup=rework_kb,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления фотографа: {e}")
            await callback.answer(
                "Заказ отправлен на доработку, но не удалось уведомить фотографа.",
                show_alert=True,
            )
            return

    await callback.answer("🔄 Заказ отправлен на доработку!", show_alert=True)
    await callback.message.edit_text(
        "🔄 <b>Заказ отправлен на доработку.</b>\n\nФотограф получил уведомление.",
        parse_mode="HTML",
    )
