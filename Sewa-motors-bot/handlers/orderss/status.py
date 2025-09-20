from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.common.constans import PHOTO_STAGES, TOTAL_STAGES
from handlers.common.utils import build_stage_message, safe_edit_message
from handlers.orderss.selection import show_order_info
from aiogram.types import CallbackQuery, FSInputFile
import logging

from utils.file_handler import (
    get_user_files,
    get_files_by_stage_summary,
)
from keyboards.inline import (
    get_photo_stage_keyboard,
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.data import (
    get_order_by_id,
    get_checklist_answers,
)
from handlers.orderss.rework import get_rework_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("order_") & F.data.contains("_"))
async def order_status_action(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    try:
        parts = data.split("_", 2)
        if len(parts) != 3 or parts[0] != "order":
            await callback.answer("Неверный формат команды.", show_alert=True)
            return
        _, status, order_id = parts

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        await state.update_data(selected_order=order_id)

        if status == "open":
            await show_order_info(callback, order)
            await callback.answer()

        elif status == "progress":
            if order.get("manager_id") != user_id:
                await callback.answer(
                    "Вы не можете продолжить этот заказ.", show_alert=True
                )
                return
            current_files = get_user_files(user_id, order_id)
            additional_files = [
                f
                for f in current_files
                if f.get("stage") == "📷 Дополнительные материалы"
            ]
            checklist = await get_checklist_answers(int(order_id))
            checklist_done = (
                checklist.get("checklist_point1") is not None
                or checklist.get("checklist_point2") is not None
            )

            if additional_files or checklist_done:
                await state.update_data(selected_order=order_id, context="rework")
                await state.set_state(OrderStates.photo_additional)

                stages_summary = get_files_by_stage_summary(user_id, order_id)
                summary_text = "📂 <b>Текущие материалы:</b>\n" + "\n".join(
                    [
                        f"• {stage}: {count} файл(ов)"
                        for stage, count in stages_summary.items()
                        if count > 0
                    ]
                )

                await callback.message.answer(
                    f"🔄 <b>Доработка заказа</b>\n\n"
                    f"🚗 <b>{order.get('brand', '')} {order.get('model', '')}</b>\n"
                    f"📋 {order.get('title', '')}\n\n"
                    f"{summary_text}\n\n"
                    f"<b>Дополнительные материалы</b>\n"
                    f"📝 Загрузите недостающие фото или видео и затем нажмите 'Завершить доработку':",
                    reply_markup=get_rework_keyboard(),
                    parse_mode="HTML",
                )
                await callback.answer()
            else:
                last_stage = None
                for stage in reversed(PHOTO_STAGES):
                    stage_files = [
                        f for f in current_files if f.get("stage") == stage["title"]
                    ]
                    if stage_files:
                        last_stage = stage
                        break
                target_stage = last_stage or PHOTO_STAGES[0]
                await state.set_state(target_stage["state"])

                stage_info = {**target_stage, "total_stages": TOTAL_STAGES}

                markup = get_photo_stage_keyboard(stage_info)
                await callback.message.answer(
                    text=build_stage_message(target_stage),
                    reply_markup=markup,
                    parse_mode="HTML",
                )
                await callback.answer()

        elif status == "done":
            files = get_user_files(user_id, order_id)
            if not files:
                await safe_edit_message(
                    callback,
                    "✅ Заказ завершён, но файлы не найдены.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="⬅️ Назад",
                                    callback_data="back_to_status_filter",
                                )
                            ]
                        ]
                    ),
                )
            else:
                await safe_edit_message(
                    callback,
                    f"✅ <b>Заказ завершён!</b>\n" f"📷 Отправлено файлов: {len(files)}",
                    parse_mode="HTML",
                )
                for file in files:
                    try:
                        document = FSInputFile(file["path"])
                        await callback.message.answer_document(document=document)
                    except Exception as e:
                        logger.error(f"Ошибка отправки файла {file['path']}: {e}")
            await callback.answer()

        else:
            await callback.answer("Неизвестный статус.", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в order_status_action: {e}")
        await callback.answer("Произошла ошибка при обработке заказа.", show_alert=True)
