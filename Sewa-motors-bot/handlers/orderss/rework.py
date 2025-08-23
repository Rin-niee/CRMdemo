from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.admin.notifications import send_files_to_admin
from handlers.common.constans import PHOTO_STAGES
from handlers.orderss.states import OrderStates
from utils.file_handler import (
    get_user_files,
    get_files_by_stage_summary,
)
from keyboards.inline import (
    get_main_menu_keyboard,
)
from utils.data import (
    update_order_status,
    get_order_by_id,
    get_dealer_by_id,
)

router = Router()


@router.callback_query(F.data.startswith("continue_order_"))
async def continue_order(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[15:]
    order = get_order_by_id(int(order_id))

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    if order.get("manager_id") != callback.from_user.id:
        await callback.answer("Вы не можете работать с этим заказом!", show_alert=True)
        return

    if order.get("status") not in ["progress", "review"]:
        await callback.answer("Этот заказ недоступен для доработки!", show_alert=True)
        return

    await state.update_data(selected_order=order_id, context="rework")

    await state.set_state(OrderStates.photo_additional)

    user_id = callback.from_user.id
    stages_summary = get_files_by_stage_summary(user_id, order_id)

    summary_lines = [
        f"• {stage}: {count} файл(ов)"
        for stage, count in stages_summary.items()
        if count > 0
    ]
    summary_text = "\n".join(summary_lines)

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
                dealer_text = "\n<b>📍 Дилер:</b>\n" + "\n".join(parts) + "\n"

    parts = [
        "🔄 <b>Доработка заказа</b>",
        "",
        f"🚗 <b>{order.get('brand', '')} {order.get('model', '')}</b>",
    ]
    if order.get("title"):
        parts.append(f"📋 {order.get('title', '')}")
    if dealer_text:
        parts.append(dealer_text.strip())
    if summary_text:
        parts.extend(["", "📂 <b>Текущие материалы:</b>", summary_text])
    parts.extend(
        [
            "",
            "<b>Дополнительные материалы</b>",
            "📝 Загрузите недостающие фото или видео и затем нажмите 'Завершить доработку':",
        ]
    )
    text = "\n".join(parts)

    await callback.message.answer(
        text,
        reply_markup=get_rework_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "finish_rework")
async def finish_rework(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_order = data.get("selected_order")
    user_id = callback.from_user.id

    if not selected_order:
        await callback.answer("Ошибка: заказ не найден в сессии!", show_alert=True)
        return

    files = get_user_files(user_id, selected_order)

    await callback.message.answer(
        f"✅ <b>Доработка завершена!</b>\n\n"
        f"📊 Общее количество файлов: {len(files)}\n"
        f"🚗 Заказ: {selected_order}\n\n"
        f"Дополнительные материалы отправлены на повторную проверку.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )

    await send_files_to_admin(selected_order, user_id, callback.bot, is_rework=True)

    update_order_status(str(selected_order), "review")

    await state.clear()


def get_rework_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Завершить доработку", callback_data="finish_rework"
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")],
        ]
    )
