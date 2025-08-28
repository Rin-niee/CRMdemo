from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from typing import Dict
from keyboards.inline import get_orders_with_opened_keyboard
from utils.data import get_open_orders_with_opened_at, get_order_by_id
from handlers.orderss.states import OrderStates
import logging
from handlers.common.utils import safe_edit_message, build_order_info_text
from keyboards.inline import (
    get_companies_keyboard,
    get_orders_keyboard,
    get_main_menu_keyboard,
    get_order_info_keyboard,
    get_precheck_decision_keyboard,
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.data import (
    get_order_by_id,
    get_orders_by_company,
    get_available_orders_by_company, 
)
from handlers.orderss.review import AdminReworkStates
from utils.data import clear_manager_for_order
from handlers.admin.notifications import notify_admin_manager_decline, notify_manager_arrived
from utils.data import update_order_status as _uos


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "orderplan_menu")
async def order_plan_menu(callback: CallbackQuery):
    """
    Показывает меню недавно открытых заказов
    
    Отображает заказы, которые были открыты недавно,
    для планирования работы на день.
    """
    orders = get_open_orders_with_opened_at()
    if not orders:
        await callback.message.edit_text("Нет недавно открытых открытых заказов.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "🕓 Недавно открытые заказы:",
        reply_markup=get_orders_with_opened_keyboard(orders),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_opened_"))
async def show_opened_order(callback: CallbackQuery, state: FSMContext):
    """
    Показывает информацию о конкретном недавно открытом заказе
    
    Args:
        callback: Callback запрос с ID заказа
        state: Контекст FSM для сохранения выбранного заказа
    """
    order_id = int(callback.data[len("order_opened_") :])
    order = get_order_by_id(order_id)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    # Сохраняем контекст и выбранный заказ
    await state.update_data(context="opened", selected_order=order_id)
    await show_order_info(callback, order, state)
    await callback.answer()


@router.callback_query(F.data == "select_order")
async def select_company_menu(callback: CallbackQuery, state: FSMContext):
    """
    Показывает меню выбора компании для работы с заказами
    
    Устанавливает состояние выбора компании в FSM.
    """
    await state.set_state(OrderStates.selecting_company)
    await safe_edit_message(
        callback, text="Выберите компанию:", reply_markup=get_companies_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("company_"))
async def company_selected_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор компании пользователем
    
    Показывает список доступных заказов для выбранной компании.
    Фильтрует заказы по доступности для текущего пользователя.
    
    Args:
        callback: Callback запрос с ID компании
        state: Контекст FSM для сохранения выбранной компании
    """
    company_id = int(callback.data[8:])
    await state.update_data(selected_company=company_id)
    await state.set_state(OrderStates.selecting_order)

    user_id = callback.from_user.id
    # Получаем заказы, доступные для пользователя в выбранной компании
    orders = get_available_orders_by_company(company_id, user_id)
    if not orders:
        await safe_edit_message(
            callback, "У этой компании пока нет заказов.", get_main_menu_keyboard()
        )
        await callback.answer()
        return

    await safe_edit_message(
        callback,
        text="Выберите заказ:",
        reply_markup=get_orders_keyboard(orders, back_button=True),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.isdigit())
async def order_selected_from_company(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор заказа пользователем
    
    Показывает детальную информацию о выбранном заказе
    и кнопки для работы с ним.
    
    Args:
        callback: Callback запрос с ID заказа
        state: Контекст FSM для сохранения выбранного заказа
    """
    order_id = int(callback.data)

    logger.info(f"Поиск заказа с ID: '{order_id}'")

    order = get_order_by_id(order_id)
    if not order:
        logger.error(f"Заказ с ID '{order_id}' не найден")
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    # Сохраняем выбранный заказ в состоянии
    await state.update_data(selected_order=order_id)
    await show_order_info(callback, order, state)


async def show_order_info(callback: CallbackQuery, order: Dict, state: FSMContext):
    """
    Показывает детальную информацию о заказе
    
    Отображает информацию о заказе и кнопки для работы с ним.
    Кнопки зависят от статуса заказа и контекста.
    
    Args:
        callback: Callback запрос
        order: Данные заказа
        state: Контекст FSM для определения контекста
    """
    info_text = build_order_info_text(order)

    state_data = await state.get_data()
    context = state_data.get("context")
    from_status_menu = context == "status"
    from_notification = context == "notification"
    
    # Определяем, пришли ли мы из меню статусов
    if not from_status_menu:
        from_status_menu = bool(
            callback.message.reply_markup
            and any(
                (btn.callback_data and "status" in btn.callback_data)
                for row in callback.message.reply_markup.inline_keyboard
                for btn in row
            )
        )
    
    buttons = []

    # Добавляем кнопки в зависимости от статуса заказа
    if order.get("status") != "done":
        # Кнопка для начала фотосессии
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅Прибыл на место", callback_data="start_photo_session"
                )
            ]
        )

        # Кнопка отказа от заказа (только для заказов в работе или на проверке)
        if order.get("status") in ("progress", "review"):
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="🙅‍♂️ Отказаться от заказа",
                        callback_data=f"decline_order_{order['id']}",
                    )
                ]
            )

    # Кнопка возврата к уведомлению
    if from_notification:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к уведомлению", callback_data="back_to_notification"
                )
            ]
        )
    else:
        # Кнопка возврата к заказам
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к заказам",
                    callback_data="back_to_status_filter"
                    if from_status_menu
                    else "back_to_orders",
                )
            ]
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
    await safe_edit_message(
        callback, text=info_text, reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "start_photo_session")
async def precheck_entry(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс предварительной проверки автомобиля
    
    Привязывает заказ к текущему пользователю и показывает
    меню выбора: начать осмотр сразу или запросить консультацию.
    
    Args:
        callback: Callback запрос
        state: Контекст FSM с выбранным заказом
    """
    data = await state.get_data()
    if not data.get("selected_order"):
        await callback.answer("Заказ не выбран!", show_alert=True)
        return

    try:
        from utils.data import update_order_status, assign_manager_to_order
        order_id = str(data.get("selected_order"))
        order = get_order_by_id(int(order_id))
        order_id2 = order.get("id")
        manager_id = order.get("manager_id")
        bot = callback.bot
        if manager_id:
            await notify_manager_arrived(bot, order_id2, manager_id)
        # Обновляем статус заказа на "progress" и назначаем менеджера
        update_order_status(order_id, "progress")
        assign_manager_to_order(order_id, callback.from_user.id)
    except Exception:
        pass
    
    # Переходим к состоянию выбора решения предварительной проверки
    await state.set_state(OrderStates.precheck_decision)
    await callback.message.answer(
        "👀 Первичная оценка авто: начните осмотр сразу или запросите консультацию у главного менеджера.",
        reply_markup=get_precheck_decision_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("decline_order_"))
async def decline_order_start(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс отказа от заказа
    
    Показывает форму для указания причины отказа.
    
    Args:
        callback: Callback запрос с ID заказа
        state: Контекст FSM
    """
    order_id = callback.data[len("decline_order_") :]
    await state.update_data(decline_order_id=order_id)
    await state.set_state(AdminReworkStates.waiting_decline_reason)
    await callback.message.answer("Укажите кратко причину отказа одним сообщением.")
    await callback.answer()


@router.message(AdminReworkStates.waiting_decline_reason, F.text)
async def decline_order_reason(message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("decline_order_id")
    reason = message.text or ""
    order = get_order_by_id(int(order_id))
    if not order:
        await message.answer("Заказ не найден.")
        await state.clear()
        return
    if order.get("manager_id") != message.from_user.id:
        await message.answer("Вы не можете отказаться от этого заказа.")
        await state.clear()
        return

    clear_manager_for_order(str(order_id))
    _uos(str(order_id), "open")

    try:
        await notify_admin_manager_decline(
            message.bot, order, message.from_user.id, reason
        )
    except Exception:
        pass
    await message.answer(
        "Вы отказались от заказа. Он снова доступен для взятия в работу."
    )
    await state.clear()
