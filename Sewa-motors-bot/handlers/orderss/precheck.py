from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import asyncio
import config

from utils.data import (
    get_order_by_id, 
    update_order_status,
    assign_manager_to_order,
    )
from handlers.orderss.states import OrderStates
from keyboards.inline import (
    get_precheck_after_video_keyboard,
)
router = Router()

_pending_customer_wait: dict[str, asyncio.Task] = {}
_active_chats: dict[str, int] = {}
_chat_manager_to_order: dict[int, str] = {}
_require_video_for_order: dict[str, bool] = {}


async def _send_manager_start_button(bot, manager_id: int, order_id: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📸 Загрузить осмотр", callback_data=f"start_photo_session_now:{order_id}")]]
    )
    await bot.send_message(manager_id, "▶️ Продолжайте осмотр.", reply_markup=kb)


async def _send_group_continue_button(bot, chat_id: int, order_id: str, thread_id: int | None = None):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📸 Загрузить осмотр", callback_data=f"start_photo_session_now:{order_id}")]]
    )
    send_kwargs = {
        "chat_id": chat_id,
        "text": "▶️ Продолжайте осмотр",
        "reply_markup": kb,
    }
    if thread_id is not None:
        send_kwargs["message_thread_id"] = thread_id

    await bot.send_message(**send_kwargs)


@router.callback_query(F.data == "precheck_start")
async def precheck_start(callback: CallbackQuery, state: FSMContext):
    from handlers.orderss.photo_session import start_photo_session
    await start_photo_session(callback, state)

#ПРОСЬБА О КОНСУЛЬТАЦИИ
@router.callback_query(F.data == "precheck_need_consult")
async def precheck_need_consult(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.precheck_wait_manager)
    await callback.message.answer("📹 Снимите короткий видео-обзор и отправьте. После отправки ожидайте дальнейшие инструкции от администратора.")
    await callback.answer()

#ПРИЕМКА ОТПРАВЛЕННОГО ВИДЕО
@router.message(OrderStates.precheck_wait_manager)
async def precheck_send_to_manager(message: Message, state: FSMContext):
    if not message.video:
        await message.answer("⚠️ Можно прислать только короткое видео.")
        return

    data = await state.get_data()
    order_id = str(data.get("selected_order"))
    order = await get_order_by_id(int(order_id))

    if not order:
        await message.answer("Заказ не найден.")
        await state.clear()
        return

    if order.get('status') == 'disabled':
        await message.answer("⛔️ Заказ закрыт администратором.")
        await state.clear()
        return

    admin_id = await config.get_admin_id()
    if not admin_id:
        await message.answer("Администратор не назначен.")
        await state.clear()
        return

    header = (
        f"📹 Предосмотр — короткое видео\n\n"
        f"🚗 {order.get('brand','')} {order.get('model','')}\n"
        f"🆔 Заказ: {order.get('id')}"
    )

    try:
        kb = get_precheck_after_video_keyboard(order_id)
        await message.bot.send_video(
            chat_id=admin_id,
            video=message.video.file_id,
            caption=header,
            reply_markup=kb
        )
        await message.answer("Видео отправлено администратору. Ожидайте решение.")

    except Exception as e:
        print(f"[ERROR] Не удалось отправить видео для заказа {order_id} админу {admin_id}: {e}")
        await message.answer(f"Произошла ошибка при отправке видео администратору.{e}")

    finally:
        await state.clear()

#ПРОДОЛЖИТЬ ОСМОТР
@router.callback_query(F.data.startswith("precheck_continue_"))
async def precheck_continue(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("precheck_continue_"):]
    order = await get_order_by_id(int(order_id))
    if order and order.get("manager_id"):
        await _send_manager_start_button(callback.bot, order["manager_id"], int(order_id))
        _active_chats.pop(str(order_id), None)
        _chat_manager_to_order.pop(order["manager_id"], None)
        _require_video_for_order.pop(str(order_id), None)
    task = _pending_customer_wait.pop(str(order_id), None)
    if task:
        task.cancel()
    await callback.answer("Продолжайте осмотр", show_alert=True)


@router.callback_query(F.data.startswith("start_photo_session_now:"))
async def start_session_now(callback: CallbackQuery, state: FSMContext):

    order_id = callback.data.split(":", 1)[1]
    try:
        await update_order_status(str(order_id), "progress")
        await assign_manager_to_order(str(order_id), callback.from_user.id)
        _active_chats.pop(str(order_id), None)
        _chat_manager_to_order.pop(callback.from_user.id, None)
        _require_video_for_order.pop(str(order_id), None)
    except Exception:
        pass

    await state.update_data(selected_order=str(order_id))
    from handlers.orderss.photo_session import start_photo_session
    await start_photo_session(callback, state)


@router.callback_query(F.data.startswith("manager_reply_"))
async def manager_reply_start(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("manager_reply_"):]
    await state.set_state(OrderStates.precheck_chat_manager)
    await state.update_data(chat_order_id=order_id)

    _chat_manager_to_order[callback.from_user.id] = order_id
    await callback.message.answer("✍️ Напишите сообщение администратору одним сообщением.")
    await callback.answer()


@router.callback_query(F.data.startswith("precheck_chat_"))
async def precheck_chat_start(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("precheck_chat_"):]
    order = await get_order_by_id(int(order_id))
    if not order or not order.get("manager_id"):
        await callback.answer("Осмотрщик не назначен.", show_alert=True)
        return

    _active_chats[order_id] = order["manager_id"]
    _chat_manager_to_order[order["manager_id"]] = order_id
    await state.set_state(OrderStates.precheck_chat)
    await state.update_data(chat_order_id=order_id)
    await callback.message.answer("✍️ Напишите сообщение осмотрщику одним сообщением")
    await callback.answer()


@router.message(OrderStates.precheck_chat, F.text & ~F.text.startswith('/'))
async def precheck_chat_bridge(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("chat_order_id")
    if not order_id:
        return
    order = await get_order_by_id(int(order_id))
    manager_id = order.get("manager_id") if order else None
    if not manager_id:
        await message.answer("Осмотрщик не назначен.")
        await state.clear()
        return

    if order and order.get('status') == 'disabled':
        _active_chats.pop(str(order_id), None)
        if manager_id in _chat_manager_to_order:
            _chat_manager_to_order.pop(manager_id, None)
        await state.clear()
        return
    manager = order.get("manager_id")
    if not manager:
        await callback.answer("Осмотрщик не назначен.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📸 Загрузить осмотр", callback_data=f"start_photo_session_now:{order_id}")]]
    )
    try:
        await message.bot.send_message(manager,
            f"💬 Сообщение от администратора:\n{message.text}", #{hint}
            reply_markup=kb,
        )
    except Exception as e:
        await callback.answer("Не удалось отправить сообщение в группу.", show_alert=True)
        print(f"Failed to send message to group {group}: {e}")


@router.message(OrderStates.precheck_chat_manager, F.text & ~F.text.startswith('/'))
async def precheck_chat_reply(message: Message, state: FSMContext):
    admin_id = await config.get_admin_id()
    if not admin_id:
        return
    if not message.text or not message.text.strip():
        return
    try:
        data = await state.get_data()
        order_id = data.get("chat_order_id") or _chat_manager_to_order.get(message.from_user.id)
        if not order_id:
            await message.bot.send_message(admin_id, f"💬 Ответ от осмотрщика:\n{message.text}")
            return

        order = await get_order_by_id(int(order_id))
        if order and order.get('status') == 'disabled':
            _active_chats.pop(str(order_id), None)
            _chat_manager_to_order.pop(message.from_user.id, None)
            await state.clear()
            return
        await message.bot.send_message(
            admin_id,
            f"💬 Сообщение от осмотрщика:\n{message.text}",
            reply_markup=get_precheck_after_video_keyboard(order_id),
        )

        await state.clear()
    except Exception:
        pass


@router.callback_query(F.data.startswith("precheck_stop_"))
async def precheck_stop(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("precheck_stop_"):]
    await update_order_status(str(order_id), "disabled")
    order = await get_order_by_id(int(order_id))
    if order and order.get("manager_id"):
        await callback.bot.send_message(order["manager_id"], "⛔️ Осмотр остановлен администратором. Заказ закрыт.")
        _active_chats.pop(str(order_id), None)
        _chat_manager_to_order.pop(order["manager_id"], None)
        _require_video_for_order.pop(str(order_id), None)
    await state.clear()

    try:
        if getattr(callback.message, "text", None):
            await callback.message.edit_text("⛔️ Осмотр остановлен. Заказ переведён в disabled.")
        else:
            await callback.message.answer("⛔️ Осмотр остановлен. Заказ переведён в disabled.")
    except Exception:
        try:
            await callback.message.answer("⛔️ Осмотр остановлен. Заказ переведён в disabled.")
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("precheck_wait_customer_"))
async def precheck_wait_customer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()


@router.callback_query(F.data.startswith("cust_no_answer_"))
async def cust_no_answer(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("cust_no_answer_"):]
    task = _pending_customer_wait.pop(str(order_id), None)
    if task:
        task.cancel()
    order = await get_order_by_id(int(order_id))
    if order and order.get("manager_id"):
        await _send_manager_start_button(callback.bot, order["manager_id"], str(order.get("id")))
    await callback.answer("Заказчик не ответил. Продолжайте осмотр.", show_alert=True)


@router.callback_query(F.data.startswith("cust_stop_"))
async def cust_stop(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("cust_stop_"):]
    task = _pending_customer_wait.pop(str(order_id), None)
    if task:
        task.cancel()
    order = await get_order_by_id(int(order_id))
    if order and order.get("manager_id"):
        await callback.bot.send_message(order["manager_id"], "⛔️ Осмотр приостановлен по решению заказчика.")
    await callback.answer("Сообщение отправлено осмотрщику.", show_alert=True)


@router.callback_query(F.data.startswith("cust_continue_"))
async def cust_continue(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data[len("cust_continue_"):]
    await state.set_state(OrderStates.precheck_video)
    await state.update_data(precheck_order_id=order_id)
    await callback.message.edit_text("✍️ Напишите комментарий от заказчика одним сообщением.")
    await callback.answer()


@router.message(OrderStates.precheck_video)
async def cust_comment_input(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("precheck_order_id")
    order = await get_order_by_id(int(order_id)) if order_id else None
    if order and order.get("manager_id"):
        await message.bot.send_message(order["manager_id"], f"✅ Решение заказчика: {message.text}\nПродолжайте осмотр.")
        await _send_manager_start_button(message.bot, order["manager_id"], str(order_id))
    task = _pending_customer_wait.pop(str(order_id), None)
    if task:
        task.cancel()
    await state.clear()

