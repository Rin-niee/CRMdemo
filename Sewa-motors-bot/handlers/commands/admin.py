from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import config
from handlers.admin.notifications import (
    send_pending_orders_to_new_admin,
    notify_managers_order_opened,
)
from keyboards.inline import (
    get_companies_with_disabled_keyboard,
    get_disabled_orders_keyboard,
)
from aiogram import F
from aiogram.types import CallbackQuery
from utils.data import (
    get_companies_with_disabled_orders,
    get_disabled_orders_by_company,
    update_order_status,
    mark_order_open,
    get_order_by_id,
)

router = Router()


@router.message(Command("become_admin"))
async def become_admin_command(message: Message):
    user_id = message.from_user.id

    if not config.is_authorized(user_id):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    if config.is_admin(user_id):
        await message.answer("✅ Вы уже являетесь администратором.")
        return

    config.set_admin_id(user_id)

    await message.answer(
        f"✅ Вы назначены администратором!\n"
        f"Теперь вам будут приходить все заявки на проверку."
    )

    await send_pending_orders_to_new_admin(message.bot, user_id)


@router.message(Command("become_manager"))
async def become_manager_command(message: Message):
    user_id = message.from_user.id

    if not config.is_admin(user_id):
        await message.answer("❌ Вы не являетесь администратором.")
        return

    config.remove_admin_id()
    await message.answer(
        f"✅ Вы сняты с роли администратора.\n"
        f"Теперь вы обычный менеджер.\n\n"
        f"⚠️ Заявки на проверку больше не будут приходить."
    )


@router.message(Command("openorders"))
async def open_orders_menu(message: Message):
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав.")
        return

    companies = get_companies_with_disabled_orders()

    if not companies:
        await message.answer("Нет заказов в статусе disabled.")
        return

    await message.answer(
        "Выберите компанию с закрытыми заказами:",
        reply_markup=get_companies_with_disabled_keyboard(companies),
    )


@router.callback_query(F.data.startswith("open_company_"))
async def openorders_company(callback: CallbackQuery):
    if not config.is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    company_id = int(callback.data[len("open_company_") :])
    orders = get_disabled_orders_by_company(company_id)

    if not orders:
        await callback.message.edit_text("У этой компании нет закрытых заказов.")
        await callback.answer()
        return

    await callback.message.edit_text(
        f"Выберите заказы для открытия ({len(orders)}):",
        reply_markup=get_disabled_orders_keyboard(orders),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("open_order_"))
async def openorders_open_order(callback: CallbackQuery):
    if not config.is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    order_id = callback.data[len("open_order_") :]
    order = get_order_by_id(int(order_id))
    company_id = order.get("company_id") if order else None
    mark_order_open(order_id)

    try:
        await notify_managers_order_opened(callback.bot, order)
    except Exception:
        pass

    await callback.answer("Заказ открыт!", show_alert=True)

    if company_id is not None:
        remaining = get_disabled_orders_by_company(int(company_id))
        if remaining:
            await callback.message.edit_text(
                f"Выберите заказы для открытия ({len(remaining)}):",
                reply_markup=get_disabled_orders_keyboard(remaining),
            )
        else:
            companies = get_companies_with_disabled_orders()
            if companies:
                await callback.message.edit_text(
                    "Выберите компанию с закрытыми заказами:",
                    reply_markup=get_companies_with_disabled_keyboard(companies),
                )
            else:
                await callback.message.edit_text(
                    "✅ Все заказы открыты. Закрытых заказов не осталось."
                )
    else:
        await callback.message.edit_reply_markup()


@router.callback_query(F.data == "openorders_back_companies")
async def openorders_back_companies(callback: CallbackQuery):

    if not config.is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    companies = get_companies_with_disabled_orders()

    if not companies:
        await callback.message.edit_text("Нет заказов в статусе disabled.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите компанию с закрытыми заказами:",
        reply_markup=get_companies_with_disabled_keyboard(companies),
    )
    
    await callback.answer()
