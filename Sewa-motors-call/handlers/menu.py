from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.main_kb import main_kb
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from utils.data import (
    get_order_by_id,
    mark_order_in_stock,
    attach_dealer_to_bid,
    dealer_info_find,
    dealer_info_create,
    get_rings_orders,
    status_disable,
)
from keyboards.main_kb import build_orders_keyboard, step_keyboard
from handlers.allinfo import show_order_info
import logging
from messages import START_TEXT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(START_TEXT, reply_markup=main_kb, parse_mode="HTML")

#возвращение на главную страницу
@router.callback_query(F.data == "go_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        START_TEXT, reply_markup=main_kb, parse_mode="HTML"
    )
    await callback.answer()

#вызов всех заказов пользователя
@router.callback_query(lambda c: c.data == "my_requests")
async def my_requests_cb(callback: types.CallbackQuery):
    orders = await get_rings_orders()

    if not orders:
        await callback.message.edit_text("У вас пока нет заявок.")
        await callback.answer()
        return

    kb = await build_orders_keyboard(orders, add_back_button=True)

    await callback.message.edit_text("Ваши заявки:", reply_markup=kb)
    await callback.answer()

#вызов данных о конкретном заказе
@router.callback_query(lambda c: c.data.startswith("request_"))
async def order_details_cb(callback: CallbackQuery):
    try:
        
        order_id = int(callback.data.split("_")[1])
        order = await get_order_by_id(order_id)
        # logger.info("DEBUG CALLBACK: %s", order)
        if not order:
            await callback.message.answer("Заказ не найден.")
            await callback.answer()
            return

        await show_order_info(callback, order, state=None)

    except ValueError:
        await callback.message.answer("Некорректный ID заказа.")
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {str(e)}")
        await callback.answer()


#вызов данных о конкретном заказе
@router.callback_query(lambda c: c.data.startswith("start_"))
async def order_details_in_stock(callback: CallbackQuery):
    order_id = callback.data[len("start_") :]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Авто в наличии",
                    callback_data=f"confirm_auto_{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Авто не в наличии",
                    callback_data=f"cancel_auto_{order_id}",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"Пожалуйста, отметьте, в наличии ли авто по заказу #{order_id}?",
        reply_markup=keyboard,
    )
    await callback.answer()

#Состояния
class DealerInfo(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()


#Начало процесса: подтверждение отказа
@router.callback_query(F.data.startswith("confirm_auto_"))
async def decline_order_confirm(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data[len("confirm_auto_"):])
    order = await get_order_by_id(order_id)
    if not order:
        await callback.message.edit_text("Заказ не найден.")
        await callback.answer()
        return

    await mark_order_in_stock(order_id)

    await callback.message.edit_text(
        f"Пожалуйста, отправьте фото дилера к заказу #{order_id}."
    )
    await state.update_data(order_id=order_id)
    await state.set_state(DealerInfo.waiting_for_photo)
    await callback.answer()


#Получение фото дилера

@router.message(DealerInfo.waiting_for_photo, F.content_type == "photo")
async def dealer_photo_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")

    file = message.photo[-1]
    file_info = await message.bot.get_file(file.file_id)
    filename = os.path.basename(file_info.file_path)
    relative_path = f"dealer/{filename}"
    os.makedirs("storage/dealer", exist_ok=True)
    await message.bot.download_file(file_info.file_path, f"storage/{relative_path}")

    await state.update_data(dealer_photo=relative_path)

    await message.answer(
        "Фото сохранено. Можете перейти дальше или вернуться назад.",
        reply_markup=step_keyboard(can_back=True, can_next=True)
    )

@router.callback_query(F.data == "next_step")
async def next_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    current_state = await state.get_state()
    if current_state == DealerInfo.waiting_for_photo.state:
        if "dealer_photo" not in data:
            await callback.answer("Сначала загрузите фото!", show_alert=True)
            return
        await callback.message.edit_text(
            "Теперь введите наименование компании дилера:",
            reply_markup=step_keyboard(can_back=True, can_next=False)
        )
        await state.set_state(DealerInfo.waiting_for_name)

    elif current_state == DealerInfo.waiting_for_name.state:
        await callback.answer("Сначала введите название компании!", show_alert=True)

@router.callback_query(F.data == "prev_step")
async def prev_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dealer_photo = data.get("dealer_photo")

    await callback.message.edit_text(
        text="Вы вернулись на шаг с фото. Можете заменить фото или идти дальше.",
        reply_markup=step_keyboard(can_back=False, can_next=True)
    )

    await state.set_state(DealerInfo.waiting_for_photo)



@router.message(DealerInfo.waiting_for_name)
async def dealer_name_received(message: types.Message, state: FSMContext):
    company_name = message.text.strip()
    if not company_name:
        await message.answer("Название компании не может быть пустым!")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    dealer_photo = data.get("dealer_photo")
    dealer = data.get("dealer_id")

    dealer_id = await dealer_info_find(company_name)
    if dealer_id:
        await attach_dealer_to_bid(dealer_id, order_id)
        await message.answer(f"Дилер найден и прикреплён к заказу #{order_id}!")
    else:
        await dealer_info_create(company_name, dealer_photo, order_id)
        await message.answer(f"Информация о дилере для заказа #{order_id} создана!")

    await state.clear()

#отмена(заказ закрывается)
@router.callback_query(F.data.startswith("cancel_auto_"))
async def decline_order_cancel(callback: CallbackQuery):
    order_id = callback.data[len("cancel_auto_") :]
    await status_disable(order_id)
    await callback.message.edit_text(
        f"Заказ #{order_id} закрыт."
    )
    await callback.answer()
