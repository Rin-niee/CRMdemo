from functools import wraps
import config
from constants import MESSAGES


def require_admin(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id

        if not await config.is_admin(user_id):
            message = "❌ Требуются права администратора"

            if hasattr(event, "data"):
                await event.answer(message, show_alert=True)
            else:
                await event.answer(message)
            return None

        return await func(event, *args, **kwargs)

    return wrapper
