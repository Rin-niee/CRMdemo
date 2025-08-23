from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.admin.notifications import (
    send_files_to_admin,
    notify_admin_manager_decline,
)
import logging
from utils.data import update_order_status, get_order_by_id, clear_manager_for_order, get_dealer_by_id

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return config.is_admin(user_id)


class AdminReworkStates(StatesGroup):
    waiting_task_text = State()
    waiting_decline_reason = State()


@router.callback_query(F.data.startswith("admin_rework_with_task_"))
async def admin_rework_with_task_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может отправлять заказы на доработку!",
            show_alert=True,
        )
        return
    order_id = callback.data[len("admin_rework_with_task_") :]
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
    if not is_admin(message.from_user.id):
        return
    task_text = message.text or ""
    order = get_order_by_id(order_id)
    if not order:
        await message.answer("Заказ не найден!")
        await state.clear()
        return
    photographer_id = order.get("manager_id")
    if not photographer_id:
        await message.answer("Осмотрщик для этого заказа не назначен!")
        await state.clear()
        return

    update_order_status(order_id, "progress")
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
    update_order_status(order_id, "review")

    await callback.answer(
        "Доп. задача завершена, материалы отправлены админу.", show_alert=True
    )
    await callback.message.edit_text("✅ Дополнительная задача завершена.")


@router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может подтверждать заказы!", show_alert=True
        )
        return

    order_id = callback.data[14:]
    order = get_order_by_id(order_id)
    manager_id = order.get("manager_id") if order else None

    update_order_status(order_id, "done")

    await callback.answer(
        "✅ Заказ подтверждён! Статус изменён на 'Выполнен'.", show_alert=True
    )
    await callback.message.edit_text(
        "✅ <b>Заказ подтверждён и завершён.</b>", parse_mode="HTML"
    )

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
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Только администратор может отправлять заказы на доработку!",
            show_alert=True,
        )
        return

    order_id = callback.data[13:]
    order = get_order_by_id(order_id)

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    update_order_status(order_id, "progress")

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
