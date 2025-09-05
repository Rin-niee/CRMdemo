import os
import sqlite3
from dotenv import load_dotenv
import asyncpg
import asyncio
import os

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

# Настройки для работы с файлами
MAX_FILE_SIZE = 40 * 1024 * 1024  # Максимальный размер файла: 40 МБ
STORAGE_PATH = "storage/files"     # Путь для хранения файлов
ALLOWED_FILE_TYPES = ["photo", "document", "video"]  # Разрешенные типы файлов
# DB_PATH = "/usr/src/app/db.sqlite3"            # Путь к базе данных

# Создаем папку для хранения файлов, если её нет
os.makedirs(STORAGE_PATH, exist_ok=True)

# Глобальные переменные для хранения ролей пользователей
_CALLER_ID = None        # ID администратора
_ALLOWED_USERS = []     # Список разрешенных пользователей
_ALLOWED_GROUPS = []     # Список разрешенных пользователей

async def load_roles_from_db():
    """
    Загружает роли пользователей из базы данных
    Обновляет глобальные переменные _CALLER_ID и _ALLOWED_USERS
    """
    global _CALLER_ID, _ALLOWED_USERS, _ALLOWED_GROUPS
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Получаем ID прозвонщика (пользователь с is_admin = 1)
        cursor.execute("SELECT id FROM users WHERE is_caller = 1")
        row = cursor.fetchone()
        _CALLER_ID = row[0] if row else None

        # Получаем список всех разрешенных пользователей
        cursor.execute("SELECT id FROM users")
        _ALLOWED_USERS = [r[0] for r in cursor.fetchall()]

        # Получаем список всех разрешенных групп
        cursor.execute("SELECT tg_id FROM groups")
        _ALLOWED_GROUPS = [r[0] for r in cursor.fetchall()]

        conn.close()
    except Exception as e:
        print(f"Ошибка загрузки ролей из БД: {e}")
        _CALLER_ID = None
        _ALLOWED_USERS = []
        _ALLOWED_GROUPS = []


def get_caller_id():
    """
    Возвращает ID администратора
    Перезагружает роли из БД перед возвратом
    """
    load_roles_from_db()
    return _CALLER_ID


def get_allowed_users():
    """
    Возвращает список всех разрешенных пользователей
    Перезагружает роли из БД перед возвратом
    """
    load_roles_from_db()
    return _ALLOWED_USERS


def get_allowed_groups():
    """
    Возвращает список всех разрешенных пользователей
    Перезагружает роли из БД перед возвратом
    """
    load_roles_from_db()
    return _ALLOWED_GROUPS


def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь администратор, False в противном случае
    """
    caller_id = get_caller_id()
    return caller_id is not None and user_id == caller_id


def is_authorized(user_id: int) -> bool:
    """
    Проверяет, авторизован ли пользователь для работы с ботом
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь авторизован, False в противном случае
    """
    allowed_users = get_allowed_users()
    return user_id in allowed_users


# Загружаем роли при импорте модуля
load_roles_from_db()
