from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from constants import MESSAGES
from keyboards.inline import (
    get_help_menu_keyboard,
    get_companies_keyboard,
    get_orders_keyboard,
)
from handlers.orderss.states import OrderStates
from utils.data import get_orders_by_company, get_orders_with_deadline
from keyboards.inline import (
    get_help_menu_keyboard,
    get_companies_keyboard,
    get_order_status_keyboard,
    get_orders_keyboard,
    get_deadline_orders_keyboard,
)
from utils.data import (
    get_orders_by_company,
    get_orders_with_deadline,
)

router = Router()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["welcome"], reply_markup=get_help_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "select_order")
@router.callback_query(F.data == "back_to_companies")
async def to_companies(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.selecting_company)
    await callback.message.edit_text(
        "Чтобы перейти к заказам, выберите компанию:",
        reply_markup=get_companies_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_orders")
async def back_to_orders(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    context = data.get("context", "company")
    company_id = data.get("selected_company")

    if context == "status":
        await callback.message.edit_text(
            "Выберите статус заказов:", reply_markup=get_order_status_keyboard()
        )
    elif context == "deadline":
        orders = get_orders_with_deadline()
        await callback.message.edit_text(
            f"📅 Заказы с дедлайном ({len(orders)}):",
            reply_markup=get_deadline_orders_keyboard(orders),
        )
    else:
        if not company_id:
            await callback.message.edit_text(
                "Сначала выберите компанию.", reply_markup=get_help_menu_keyboard()
            )
            await callback.answer()
            return

        orders = get_orders_by_company(company_id)
        if not orders:
            await callback.message.edit_text(
                "У этой компании пока нет заказов.",
                reply_markup=get_help_menu_keyboard(),
            )
            await callback.answer()
            return

        await state.set_state(OrderStates.selecting_order)
        await callback.message.edit_text(
            "Выберите заказ:",
            reply_markup=get_orders_keyboard(orders, back_button=True),
        )

    await callback.answer()
