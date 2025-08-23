from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.inline import (
    get_order_status_keyboard,
    get_orders_with_opened_keyboard,
)

from utils.data import (
    get_open_orders_with_opened_at,
)

router = Router()


@router.message(Command("myorders"))
async def my_orders_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите статус заказов:", reply_markup=get_order_status_keyboard()
    )


@router.message(Command("orderplan"))
async def order_plan_command(message: Message, state: FSMContext):
    await state.clear()
    orders = get_open_orders_with_opened_at()
    if not orders:
        await message.answer("Нет недавно открытых открытых заказов.")
        return

    await message.answer(
        "🕓 Недавно открытые заказы:",
        reply_markup=get_orders_with_opened_keyboard(orders),
    )
