from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from constants import MESSAGES
import config


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для авторизации пользователей
    
    Проверяет права доступа пользователя перед выполнением любого действия.
    Блокирует неавторизованных пользователей и отправляет сообщение об ошибке.
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Основной метод middleware, вызывается перед каждым действием пользователя
        
        Args:
            handler: Функция-обработчик, которая должна выполниться
            event: Событие от Telegram (сообщение, callback и т.д.)
            data: Дополнительные данные для обработчика
            
        Returns:
            Результат выполнения обработчика или None если доступ запрещен
        """
        # Получаем ID пользователя из события
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        # Если не удалось получить ID пользователя, пропускаем обработку
        if user_id is None:
            return await handler(event, data)

        # Проверяем авторизацию пользователя
        if not self._is_authorized(user_id, event):
            # Если пользователь не авторизован, отправляем сообщение об ошибке
            if isinstance(event, Message):
                await event.answer(MESSAGES["unauthorized"])
            elif isinstance(event, CallbackQuery):
                await event.answer(MESSAGES["unauthorized"], show_alert=True)
            return None

        # Если пользователь авторизован, выполняем обработчик
        return await handler(event, data)

    def _is_authorized(self, user_id: int, event: TelegramObject) -> bool:
        """
        Проверяет, авторизован ли пользователь для выполнения действия
        
        Args:
            user_id: ID пользователя для проверки
            event: Событие от Telegram для дополнительной логики
            
        Returns:
            True если пользователь авторизован, False в противном случае
        """
        # Разрешаем всем пользователям без ограничений
        # TODO: В будущем здесь должна быть реальная проверка авторизации
        return True
