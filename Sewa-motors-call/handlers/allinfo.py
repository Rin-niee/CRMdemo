from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from utils.data import(
    get_company_info,
)


async def show_order_info(callback: CallbackQuery, order: dict, state=None):
    """
    Показывает детальную информацию о заказе с кнопками действий.
    
    Args:
        callback: CallbackQuery с нажатой кнопкой
        order: словарь с данными заказа
        state: FSMContext, если нужно работать с состояниями (можно None)
    """
    try:
        order_text = f"🚗 Заказ #{order.get('id')}\n"
        order_text += f"URL: {order.get('url_users', 'Неизвестно')}\n"
        order_company = await get_company_info(order.get("company_id"))
        if order_company:
            info_parts = []
            info_parts.append(
                "Компания: " + (order_company.get("name") or "Неизвестно") +
                "\nИНН: " + (order_company.get("INN") or "Неизвестно") +
                "\nАдрес: " + (order_company.get("OGRN") or "Неизвестно") +
                "\nТелефон: " + (order_company.get("phone") or "Неизвестно") +
                "\nE-mail: " + (order_company.get("email") or "Неизвестно")
            )
            order_text += info_parts
        buttons = [
            [InlineKeyboardButton(text="✅ Начать", callback_data=f"start_{order['id']}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_requests")]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(order_text, reply_markup=kb)
        
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {str(e)}")
        await callback.answer()