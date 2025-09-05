from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.data import (
    get_company_info,
)
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Открытые заявки для прозвонов", callback_data="my_requests")],
    ]
)

def build_orders_keyboard(orders, add_back_button=False):
    """
    Формирует InlineKeyboardMarkup для списка заказов.

    Args:
        orders (list[dict]): Список заказов с ключами 'id', 'company_id', 'url_users'
        add_back_button (bool): Если True, добавляет кнопку "Назад"

    Returns:
        InlineKeyboardMarkup: готовая клавиатура
    """
    buttons = []

    for order in orders:
        company_id = order.get('company_id')
        company = get_company_info(company_id) if company_id else None
        company_name = company.get('name', 'Неизвестно') if company else 'Неизвестно'
        url = order.get('url_users', 'Неизвестно')

        text = f"{order['id']} - {company_name} - {url}"
        callback_data = f"request_{order['id']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
        # logger.info("DEBUG CALLBACK: %s", callback_data)

    if add_back_button:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def step_keyboard(can_back=True, can_next=True):
    buttons = []
    if can_back:
        buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data="prev_step"))
    if can_next:
        buttons.append(InlineKeyboardButton(text="➡ Вперед", callback_data="next_step"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])