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
        order_company = get_company_info(order.get("company_id"))
        order_text += f"Компания: {order_company.get('name', 'Неизвестно')}\n"
        order_text += f"ИНН: {order_company.get('INN', 'Неизвестно')}\n"
        order_text += f"ОРГН: {order_company.get('OGRN', 'Неизвестно')}\n"
        order_text += f"Адрес: {order_company.get('adress', 'Неизвестно')}\n"

        # Кнопки
        buttons = [
            [InlineKeyboardButton(text="✅ Начать", callback_data=f"start_{order['id']}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_requests")]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(order_text, reply_markup=kb)
        
        await callback.answer()
    except Exception as e:
        # логируем или показываем ошибку пользователю
        await callback.message.answer(f"Произошла ошибка: {str(e)}")
        await callback.answer()