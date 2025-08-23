from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.common.constans import PHOTO_STAGES, TOTAL_STAGES
from handlers.common.utils import (
    build_stage_message,
    get_next_stage,
    get_stage_by_state,
)
from handlers.admin.notifications import send_files_to_admin
from utils.file_handler import get_stage_files, get_user_files
from keyboards.inline import (
    get_photo_stage_keyboard,
    get_main_menu_keyboard,
    get_checklist_question_keyboard,
)

from utils.data import update_order_status, assign_manager_to_order, get_order_by_id
from handlers.admin.notifications import notify_admin_manager_assignment
from typing import List
import asyncio
from handlers.orderss.states import OrderStates
from handlers.orderss.rework import finish_rework
from keyboards.inline import get_checklist_multichoice_keyboard

router = Router()


@router.callback_query(F.data == "start_photo_session")
async def start_photo_session(callback: CallbackQuery, state: FSMContext):
    """
    Начинает фотосессию автомобиля
    
    Проверяет доступность заказа, назначает менеджера,
    уведомляет администратора и показывает первый этап фотосъемки.
    
    Args:
        callback: Callback запрос
        state: Контекст FSM с выбранным заказом
    """
    data = await state.get_data()
    selected_order = data.get("selected_order")

    if not selected_order:
        await callback.answer("Заказ не выбран!", show_alert=True)
        return

    user_id = callback.from_user.id

    # Получаем данные заказа
    order = get_order_by_id(int(selected_order))
    
    # Проверяем, не завершен ли заказ
    if order and order.get("status") == "done":
        await callback.answer(
            "Заказ завершён и недоступен для редактирования.", show_alert=True
        )
        return

    # Проверяем, не взят ли заказ другим менеджером
    if order and order.get("manager_id") and order.get("manager_id") != user_id:
        await callback.answer(
            "Этот заказ уже в работе у другого сотрудника.", show_alert=True
        )
        return

    # Уведомляем администратора о назначении менеджера
    if order and not order.get("manager_id"):
        try:
            await notify_admin_manager_assignment(callback.bot, order, user_id)
        except Exception:
            pass
    
    # Асинхронно обновляем статус заказа и назначаем менеджера
    asyncio.create_task(update_order_async(selected_order, user_id))

    # Получаем первый этап фотосессии
    first_stage = PHOTO_STAGES[0]
    await state.set_state(first_stage["state"])
    await state.update_data(selected_order=selected_order)

    stage_info = {**first_stage, "total_stages": TOTAL_STAGES}

    # Создаем клавиатуру для первого этапа
    markup = get_photo_stage_keyboard(stage_info)
    try:
        selected_order_id = selected_order
        # Добавляем кнопку отказа от заказа
        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="🙅‍♂️ Отказаться от заказа",
                    callback_data=f"decline_order_{selected_order_id}",
                )
            ]
        )

    except Exception:
        pass

    # Отправляем сообщение с первым этапом
    await callback.message.answer(
        text=build_stage_message(first_stage),
        reply_markup=markup,
        parse_mode="HTML",
    )
    await callback.answer("Старт!")


async def update_order_async(selected_order, user_id):
    """
    Асинхронно обновляет статус заказа и назначает менеджера
    
    Args:
        selected_order: ID заказа
        user_id: ID менеджера
    """
    try:
        order_id_str = str(selected_order)
        update_order_status(order_id_str, "progress")
        assign_manager_to_order(order_id_str, user_id)
    except Exception:
        pass


@router.callback_query(F.data == "next_stage")
async def next_stage(callback: CallbackQuery, state: FSMContext):
    """
    Переходит к следующему этапу фотосессии
    
    Проверяет наличие файлов на текущем этапе,
    переходит к следующему или завершает фотосессию.
    
    Args:
        callback: Callback запрос
        state: Контекст FSM
    """
    current_state = await state.get_state()
    current_stage = get_stage_by_state(current_state)

    # Если это дополнительный этап, завершаем фотосессию
    if current_state == OrderStates.photo_additional.state:
        await finish_rework(callback, state)
        return

    # Проверяем наличие файлов на обязательных этапах
    if current_stage and current_stage["required"]:
        data = await state.get_data()
        selected_order = data.get("selected_order")

        if not selected_order:
            await callback.answer("Ошибка: заказ не найден!", show_alert=True)
            return

        # Получаем файлы текущего этапа
        files = get_stage_files(
            callback.from_user.id, selected_order, current_stage["title"]
        )
        if not files:
            await callback.answer("Загрузите хотя бы один файл!", show_alert=True)
            return

    # Получаем информацию о следующем этапе
    next_stage_info = get_next_stage(current_state)
    if not next_stage_info:
        # Если этапов больше нет, завершаем фотосессию
        asyncio.create_task(finish_photo_session_async(callback, state))
        return

    # Переходим к следующему этапу
    await state.set_state(next_stage_info["state"])
    stage_info = {**next_stage_info, "total_stages": TOTAL_STAGES}

    # Создаем клавиатуру для следующего этапа
    markup = get_photo_stage_keyboard(stage_info)
    try:
        data = await state.get_data()
        selected_order_id = data.get("selected_order")
        if selected_order_id:
            # Добавляем кнопку отказа от заказа
            markup.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="🙅‍♂️ Отказаться от заказа",
                        callback_data=f"decline_order_{selected_order_id}",
                    )
                ]
            )

    except Exception:
        pass

    # Отправляем сообщение со следующим этапом
    await callback.message.edit_text(
        text=build_stage_message(next_stage_info),
        reply_markup=markup,
        parse_mode="HTML",
    )
    await callback.answer("Следующий этап!")


async def finish_photo_session_async(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_order = data.get("selected_order")
    user_id = callback.from_user.id

    current_state = await state.get_state()
    if current_state == OrderStates.photo_additional.state:
        await finish_rework(callback, state)
        return

    if not selected_order:
        await callback.message.answer(
            "Фотосессия завершена!", reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        await callback.answer("Готово!")
        return

    missing_stages = []
    for stage in PHOTO_STAGES:
        if stage["required"]:
            files = get_stage_files(user_id, selected_order, stage["title"])
            if not files:
                missing_stages.append(
                    stage["title"].replace("📸 ", "").replace("🎥 ", "")
                )

    if missing_stages:
        await callback.answer(
            f"Не загружены: {', '.join(missing_stages)}", show_alert=True
        )
        return

    await state.set_state(OrderStates.checklist_q1)
    await callback.message.answer(
        "✅ Фото и видео получены.\n\nВопрос 1: Состояние бампера?",
        reply_markup=get_checklist_multichoice_keyboard(
            1, [("Отлично", "отлично"), ("Хорошо", "хорошо"), ("Плохо", "плохо")]
        ),
    )
    await callback.answer()


async def send_to_admin_async(selected_order, user_id, bot):
    try:
        await send_files_to_admin(selected_order, user_id, bot, is_rework=False)
        update_order_status(str(selected_order), "review")
    except Exception:
        pass
