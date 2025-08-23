from typing import Optional, Dict
import logging
from aiogram.types import CallbackQuery
from handlers.common.constans import STAGE_INDEX, PHOTO_STAGES, TOTAL_STAGES
from handlers.orderss.states import OrderStates
from utils.data import get_dealer_by_id, get_company_by_id

logger = logging.getLogger(__name__)


def get_stage_by_state(state) -> Optional[Dict]:
    if state == OrderStates.photo_additional:
        return {
            "state": OrderStates.photo_additional,
            "title": "📷 Дополнительные материалы",
            "description": "Добавьте дополнительные фото или видео при необходимости",
            "required": False,
            "stage_num": len(PHOTO_STAGES) + 1,
        }
    index = STAGE_INDEX.get(state)
    return PHOTO_STAGES[index] if index is not None else None


def get_next_stage(current_state) -> Optional[Dict]:
    current_index = STAGE_INDEX.get(current_state)
    if current_index is not None and current_index < len(PHOTO_STAGES) - 1:
        return PHOTO_STAGES[current_index + 1]
    return None


def build_order_info_text(order: Dict) -> str:
    info_parts = [f"🚗 <b>{order.get('brand', '')} {order.get('model', '')}</b>"]

    if order.get("url"):
        info_parts.append(f"<b>{order['url']}</b>")

    company_id = order.get("company_id")
    if company_id:
        company = get_company_by_id(company_id)
        if company:
            info_parts.append(
                "\n🏢<b> Компания: </b>\n"
                + "\n".join(
                    [
                        company.get("name", "Неизвестно"),
                    ]
                )
            )
    dealer_id = order.get("dealers_id")
    if dealer_id:
        dealer = get_dealer_by_id(dealer_id)
        if dealer:
            dealer_info = []
            if dealer.get("name"):
                dealer_info.append(dealer["name"])
            if dealer.get("phone"):
                dealer_info.append(f"{dealer['phone']}")
            if dealer.get("address"):
                dealer_info.append(f"{dealer['address']}")
            info_parts.append("\n<b>📍 Дилер:</b>\n" + "\n".join(dealer_info))

    info_parts.append("\nГотовы начать съемку автомобиля?")

    return "\n".join(info_parts)


def build_stage_message(stage: Dict) -> str:
    return (
        f"<b>{stage['title']}</b>\n"
        f"Этап {stage['stage_num']} из {TOTAL_STAGES}\n\n"
        f"📝 {stage['description']}\n\n"
        f"Отправьте одно или несколько фото/видео:"
    )


async def safe_edit_message(
    callback: CallbackQuery, text: str, reply_markup=None, **kwargs
):
    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        await callback.message.answer(text=text, reply_markup=reply_markup, **kwargs)
