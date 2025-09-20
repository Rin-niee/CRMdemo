from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Dict
from handlers.orderss.states import OrderStates
import logging
from handlers.common.utils import safe_edit_message, build_order_info_text
from keyboards.inline import (
    get_companies_keyboard,
    get_orders_keyboard,
    get_main_menu_keyboard,
    get_precheck_decision_keyboard,
    get_orders_with_opened_keyboard_for_decline,
    get_orders_with_opened_keyboard,
)
from utils.data import (
    get_order_by_id,
    get_available_orders_by_company, 
    get_all_orders_for_me,
    get_open_orders_with_opened_at, 
    clear_manager_for_order,
    update_order_status,
    assign_manager_to_order
)
from handlers.admin.notifications import notify_admin_manager_decline, notify_manager_arrived


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "orderplan_menu")
async def order_plan_menu(callback: CallbackQuery):
    """
    Показывает меню недавно открытых заказов
    
    Отображает заказы, которые были открыты недавно,
    для планирования работы на день.
    """
    orders = await get_open_orders_with_opened_at()
    if not orders:
        await callback.message.edit_text("Нет недавно открытых открытых заказов.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "🕓 Недавно открытые заказы:",
        reply_markup=get_orders_with_opened_keyboard(orders),
    )
    await callback.answer()



@router.callback_query(F.data == "all_my_orders")
async def declare_menu(callback: CallbackQuery):
    """
    Показывает меню заказов пользователя от которого хочет отказаться.
    """
    user_id = callback.from_user.id

    orders = await get_all_orders_for_me(user_id)
    if not orders:
        await callback.message.edit_text("У вас нет заказов.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "🙅‍♂️ Выберите, от какого из заказов вы хотите отказаться:",
        reply_markup=get_orders_with_opened_keyboard_for_decline(orders),
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
    order = await get_order_by_id(order_id)

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
        callback, text="Выберите компанию:", reply_markup=await get_companies_keyboard()
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
    orders = await get_available_orders_by_company(company_id, user_id)
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

    order = await get_order_by_id(order_id)
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
    info_text, photo = await build_order_info_text(order)

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
    
    if photo:
        await callback.message.answer_photo(photo=photo, caption=info_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")


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
        order_id = str(data.get("selected_order"))
        order = await get_order_by_id(int(order_id))
        order_id2 = order.get("id")
        manager_id = order.get("manager_id")
        bot = callback.bot
        if manager_id:
            await notify_manager_arrived(bot, order_id2, manager_id)
        # Обновляем статус заказа на "progress" и назначаем менеджера
        await update_order_status(order_id, "progress")
        await assign_manager_to_order(order_id, callback.from_user.id)
    except Exception:
        pass
    
    # Выбор решения предварительной проверки
    await state.set_state(OrderStates.precheck_decision)
    await callback.message.answer(
        "👀 Первичная оценка авто: начните осмотр сразу или запросите консультацию у главного менеджера.",
        reply_markup=get_precheck_decision_keyboard(),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("decline_order_"))
async def decline_order_start(callback: CallbackQuery):
    order_id = int(callback.data[len("decline_order_") :])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, отказаться",
                    callback_data=f"confirm_decline_{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет, оставить",
                    callback_data=f"cancel_decline_{order_id}",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"Вы точно хотите отказаться от заказа #{order_id}?",
        reply_markup=keyboard,
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_decline_"))
async def decline_order_confirm(callback: CallbackQuery):
    order_id = callback.data[len("confirm_decline_") :]

    order = await get_order_by_id(int(order_id))
    if not order:
        await callback.message.edit_text("Заказ не найден.")
        await callback.answer()
        return

    if order.get("manager_id") != callback.from_user.id:
        await callback.message.edit_text("Вы не можете отказаться от этого заказа.")
        await callback.answer()
        return

    await clear_manager_for_order(int(order_id))
    await update_order_status(int(order_id), "open")

    try:
        await notify_admin_manager_decline(
            callback.bot, order, callback.from_user.id, reason=None
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"Вы отказались от заказа #{order_id}. Он снова доступен для взятия."
    )
    await callback.answer()


#отмена
@router.callback_query(F.data.startswith("cancel_decline_"))
async def decline_order_cancel(callback: CallbackQuery):
    order_id = callback.data[len("cancel_decline_") :]

    await callback.message.edit_text(
        f"Отказ от заказа #{order_id} отменён."
    )
    await callback.answer()
