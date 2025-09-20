from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_order_status_keyboard, get_filtered_orders_keyboard
from utils.data import (
    get_orders_by_status,
    get_all_open_orders,
    get_order_by_id,
    get_dealer_by_id,
    save_arrival_time,
    get_all_open_orders_for_me
)
from handlers.orderss.selection import show_order_info
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.orderss.selection import show_order_info
from handlers.admin.notifications import notify_manager_departure

router = Router()


@router.callback_query(F.data == "my_orders_menu")
async def my_orders_button(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите статус заказов:", reply_markup=get_order_status_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("status_"))
async def filter_orders_by_status(callback: CallbackQuery, state: FSMContext):
    status = callback.data[7:]
    user_id = callback.from_user.id

    if status == "open":
        orders = await get_all_open_orders_for_me(user_id)
    else:
        orders = await get_orders_by_status(user_id, [status])

    status_names = {
        "open": "Открытые",
        "progress": "В процессе",
        "review": "На проверке",
        "done": "Завершённые",
    }
    status_display = status_names.get(status, status)

    if not orders:
        await callback.message.edit_text(
            f"Нет заказов со статусом '{status_display}'.",
            reply_markup=get_order_status_keyboard(),
        )
        await callback.answer()
        return

    await state.update_data(context="status")
    await callback.message.edit_text(
        f"📋 Заказы со статусом: {status_display} ({len(orders)})",
        reply_markup=get_filtered_orders_keyboard(orders),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_status_filter")
async def back_to_status_menu(callback: CallbackQuery):
    await callback.message.answer(
        "Выберите статус заказов:", reply_markup=get_order_status_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_time_"))
async def order_time(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    order_id = int(data_parts[2])

    times = [60, 90, 120, 150, 180, 'more']

    inline_buttons = []
    for t in times:
        if t == 'more':
            text = "Более 3 ч"
            callback_data = f"set_arrival_{order_id}_more"
        else:
            text = f"{t/60:.1f} ч"
            callback_data = f"set_arrival_{order_id}_{t}"
        inline_buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

    kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)

    await callback.message.edit_reply_markup(reply_markup=kb)

    await callback.answer("Выберите время прибытия:")


@router.callback_query(F.data.startswith("set_arrival_"))
async def set_arrival_time(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    order_id = int(parts[2])
    choice = parts[3]
    manager_id = callback.from_user.id
    now = datetime.now()

    if choice != "more":
        minutes = int(choice)
        arrival_time = now + timedelta(minutes=minutes)
        note = arrival_time.strftime("%Y-%m-%d %H:%M")
    else:
        arrival_time = None
        note = "более 3 часов"
    await save_arrival_time(order_id, arrival_time, manager_id, status="progress")
    await callback.message.edit_reply_markup(None)

    order = await get_order_by_id(order_id)
    if order:
        await state.update_data(selected_order=order_id)
        await show_order_info(callback, order, state)
        bot = callback.bot
        await notify_manager_departure(bot, order_id, manager_id, note)

    await callback.answer(f"Время прибытия установлено: {note}")


@router.callback_query(F.data.startswith("order_status_"))
async def order_details_from_status(callback: CallbackQuery, state: FSMContext):
    order_id_str = callback.data.replace("order_status_", "")
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback.answer("Неверный идентификатор заказа.", show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order.get("status") == "done":
        await callback.answer(
            "Заказ завершён. Редактирование недоступно.", show_alert=True
        )
        return

    origin_text = (callback.message.text or "").lower()
    from_notification = ("открыт новый заказ" in origin_text) or (
        "открытый заказ ожидает" in origin_text
    )
    await state.update_data(
        context=("notification" if from_notification else "status"),
        selected_order=order_id,
    )

    await show_order_info(callback, order, state)
    await callback.answer()


@router.callback_query(F.data == "back_to_notification")
async def back_to_notification(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("selected_order")

    if not order_id:
        await callback.answer()
        return

    order = await get_order_by_id(int(order_id))

    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    dealer_text = ""
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
                dealer_text = "\n<b>📍 Дилер:</b>\n" + "\n".join(parts)
    text = (
        "🔔 <b>Открытый заказ ожидает осмотрщика</b>\n\n"
        f"🚗 <b>{order.get('brand','')} {order.get('model','')}</b>\n"
        f"🆔 Заказ: {order.get('id')}" + dealer_text + "\n\n"
        "Нажмите кнопку ниже, чтобы взять заказ."
    )

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
    await callback.message.edit_text(text, reply_markup=open_kb, parse_mode="HTML")
    await callback.answer()
