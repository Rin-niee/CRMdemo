from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from constants import MESSAGES
from keyboards.inline import (
    get_help_menu_keyboard,
    get_companies_keyboard,
)
from handlers.auth.decorators import require_admin
from utils.data import ensure_user_exists

router = Router()


@router.message(CommandStart())
@router.message(Command("help"))
async def welcome_command(message: Message, state: FSMContext):
    """
    Обработчик команд /start и /help
    
    Приветствует пользователя, создает запись в БД если её нет,
    очищает состояние FSM и показывает главное меню помощи.
    
    Args:
        message: Сообщение от пользователя
        state: Контекст конечного автомата состояний
    """
    try:
        # Создаем запись пользователя в БД если её нет
        ensure_user_exists(message.from_user.id)
    except Exception:
        # Игнорируем ошибки при создании пользователя
        pass
    
    # Очищаем состояние FSM
    await state.clear()
    
    # Отправляем приветственное сообщение с клавиатурой помощи
    await message.answer(MESSAGES["welcome"], reply_markup=get_help_menu_keyboard(message.from_user.id))


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext):
    """
    Обработчик команды /menu
    
    Показывает меню выбора компании для работы с заказами.
    Создает запись пользователя в БД если её нет.
    
    Args:
        message: Сообщение от пользователя
        state: Контекст конечного автомата состояний
    """
    try:
        # Создаем запись пользователя в БД если её нет
        ensure_user_exists(message.from_user.id)
    except Exception:
        # Игнорируем ошибки при создании пользователя
        pass
    
    # Очищаем состояние FSM
    await state.clear()
    
    # Отправляем сообщение с выбором компании
    await message.answer(
        "Чтобы перейти к заказам, выберите компанию:",
        reply_markup=get_companies_keyboard(),
    )
