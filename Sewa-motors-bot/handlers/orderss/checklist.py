from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.orderss.states import OrderStates
from keyboards.inline import (
    get_checklist_question_keyboard,
    get_main_menu_keyboard,
    get_checklist_multichoice_keyboard,
)
from utils.data import (
    set_checklist_answer,
    get_checklist_answers,
    update_order_status,
    set_checklist_answer_text,
)
from handlers.admin.notifications import send_files_to_admin

router = Router()


def _extract_value(cbdata: str) -> str:
    parts = cbdata.split(":", 2)
    return parts[2] if len(parts) == 3 else ""


@router.callback_query(OrderStates.checklist_q1, F.data.startswith("chk:1:"))
async def on_checklist_q1(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = int(data["selected_order"])
    value_text = _extract_value(callback.data)
    set_checklist_answer_text(order_id, 1, value_text)

    await state.set_state(OrderStates.checklist_q2)
    
    await callback.message.edit_text(
        "Вопрос 2: Уровень топлива в баке?",
        reply_markup=get_checklist_multichoice_keyboard(
            2, [("Полный", "полный"), ("Половина", "половина"), ("Мало", "мало")]
        ),
    )
    await callback.answer()


@router.callback_query(OrderStates.checklist_q2, F.data.startswith("chk:2:"))
async def on_checklist_q2(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = int(data["selected_order"])
    value_text = _extract_value(callback.data)
    set_checklist_answer_text(order_id, 2, value_text)

    await callback.message.answer(
        "📤 Чек-лист заполнен. Отправляю материалы администратору…"
    )
    await send_files_to_admin(
        str(order_id), callback.from_user.id, callback.bot, is_rework=False
    )
    update_order_status(str(order_id), "review")

    await callback.message.answer(
        "✅ Готово. Материалы ушли на проверку.", reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
    await callback.answer("Завершено!")
