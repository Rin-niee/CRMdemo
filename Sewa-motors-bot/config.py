import os
from dotenv import load_dotenv
import asyncpg
import redis.asyncio as aioredis

# Загружаем переменные окружения из файла .env
load_dotenv(override=True)
BASE_URL = os.getenv("BASE_URL")
DB_NAME = os.getenv("DB_NAME", "crm_db")
DB_USER = os.getenv("DB_USER", "crm_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "securepassword")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

CRM_TOKEN = os.getenv("CRM_TOKEN")

redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)

# Настройки для работы с файлами
MAX_FILE_SIZE = 40 * 1024 * 1024  # Максимальный размер файла: 40 МБ
STORAGE_PATH = "storage/files"     # Путь для хранения файлов
ALLOWED_FILE_TYPES = ["photo", "document", "video"]  # Разрешенные типы файлов
# DB_PATH = "/usr/src/app/db.sqlite3"            # Путь к базе данных

# Создаем папку для хранения файлов, если её нет
os.makedirs(STORAGE_PATH, exist_ok=True)

# Глобальные переменные для хранения ролей пользователей
_ADMIN_ID = None        # ID администратора
_ALLOWED_USERS = []     # Список разрешенных пользователей
_ALLOWED_GROUPS = []     # Список разрешенных пользователей

async def load_roles_from_db():
    """
    Загружает роли пользователей из базы данных
    Обновляет глобальные переменные _ADMIN_ID и _ALLOWED_USERS
    """
    global _ADMIN_ID, _ALLOWED_USERS, _ALLOWED_GROUPS
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        # cursor = conn.cursor()

        # # Получаем ID администратора (пользователь с is_admin = 1)
        # cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
        # row = cursor.fetchone()
        # _ADMIN_ID = row[0] if row else None

        # # Получаем список всех разрешенных пользователей
        # cursor.execute("SELECT id FROM users")
        # _ALLOWED_USERS = [r[0] for r in cursor.fetchall()]

        # # Получаем список всех разрешенных групп
        # cursor.execute("SELECT tg_id FROM groups")
        # _ALLOWED_GROUPS = [r[0] for r in cursor.fetchall()]

        row = await conn.fetchrow("SELECT id FROM users WHERE is_admin = True")
        _ADMIN_ID = row["id"] if row else None

        rows = await conn.fetch("SELECT id FROM users")
        _ALLOWED_USERS = [r["id"] for r in rows]

        rows = await conn.fetch("SELECT tg_id FROM groups")
        _ALLOWED_GROUPS = [r["tg_id"] for r in rows]


        await conn.close()
    except Exception as e:
        print(f"Ошибка загрузки ролей из БД: {e}")
        _ADMIN_ID = None
        _ALLOWED_USERS = []
        _ALLOWED_GROUPS = []


async def get_admin_id():
    """
    Возвращает ID администратора
    Перезагружает роли из БД перед возвратом
    """
    await load_roles_from_db()
    return _ADMIN_ID


async def get_allowed_users():
    """
    Возвращает список всех разрешенных пользователей
    Перезагружает роли из БД перед возвратом
    """
    await load_roles_from_db()
    return _ALLOWED_USERS


async def get_allowed_groups():
    """
    Возвращает список всех разрешенных пользователей
    Перезагружает роли из БД перед возвратом
    """
    await load_roles_from_db()
    return _ALLOWED_GROUPS


async def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь администратор, False в противном случае
    """
    admin_id = await get_admin_id()
    return admin_id is not None and user_id == admin_id


async def is_authorized(user_id: int) -> bool:
    """
    Проверяет, авторизован ли пользователь для работы с ботом
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь авторизован, False в противном случае
    """
    allowed_users = await get_allowed_users()
    return user_id in allowed_users


async def set_admin_id(user_id: int):
    """
    Назначает пользователя администратором
    Сначала сбрасывает все права администратора, затем назначает нового
    
    Args:
        user_id: ID пользователя, которого назначают администратором
    """
    global _ADMIN_ID
    conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
    )
    cursor = conn.cursor()

    # Сбрасываем права администратора у всех пользователей
    cursor.execute("UPDATE users SET is_admin = 0")
    # Назначаем права администратора указанному пользователю
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    await conn.close()

    # Обновляем глобальную переменную
    _ADMIN_ID = user_id


async def remove_admin_id():
    """
    Убирает права администратора у всех пользователей
    Используется для сброса административных прав
    """
    global _ADMIN_ID
    conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
    )
    cursor = conn.cursor()

    # Сбрасываем права администратора у всех пользователей
    cursor.execute("UPDATE users SET is_admin = 0")
    conn.commit()
    await conn.close()

    # Обновляем глобальную переменную
    _ADMIN_ID = None


# Загружаем роли при импорте модуля
load_roles_from_db
