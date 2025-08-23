import os
import sqlite3
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv(override=True)

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройки для работы с файлами
MAX_FILE_SIZE = 40 * 1024 * 1024  # Максимальный размер файла: 40 МБ
STORAGE_PATH = "storage/files"     # Путь для хранения файлов
ALLOWED_FILE_TYPES = ["photo", "document", "video"]  # Разрешенные типы файлов
DB_PATH = "/usr/src/app/db.sqlite3"            # Путь к базе данных

# Создаем папку для хранения файлов, если её нет
os.makedirs(STORAGE_PATH, exist_ok=True)

# Глобальные переменные для хранения ролей пользователей
_ADMIN_ID = None        # ID администратора
_ALLOWED_USERS = []     # Список разрешенных пользователей


def load_roles_from_db():
    """
    Загружает роли пользователей из базы данных
    Обновляет глобальные переменные _ADMIN_ID и _ALLOWED_USERS
    """
    global _ADMIN_ID, _ALLOWED_USERS
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Получаем ID администратора (пользователь с is_admin = 1)
        cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
        row = cursor.fetchone()
        _ADMIN_ID = row[0] if row else None

        # Получаем список всех разрешенных пользователей
        cursor.execute("SELECT id FROM users")
        _ALLOWED_USERS = [r[0] for r in cursor.fetchall()]

        conn.close()
    except Exception as e:
        print(f"Ошибка загрузки ролей из БД: {e}")
        _ADMIN_ID = None
        _ALLOWED_USERS = []


def get_admin_id():
    """
    Возвращает ID администратора
    Перезагружает роли из БД перед возвратом
    """
    load_roles_from_db()
    return _ADMIN_ID


def get_allowed_users():
    """
    Возвращает список всех разрешенных пользователей
    Перезагружает роли из БД перед возвратом
    """
    load_roles_from_db()
    return _ALLOWED_USERS


def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь администратор, False в противном случае
    """
    admin_id = get_admin_id()
    return admin_id is not None and user_id == admin_id


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


def set_admin_id(user_id: int):
    """
    Назначает пользователя администратором
    Сначала сбрасывает все права администратора, затем назначает нового
    
    Args:
        user_id: ID пользователя, которого назначают администратором
    """
    global _ADMIN_ID
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Сбрасываем права администратора у всех пользователей
    cursor.execute("UPDATE users SET is_admin = 0")
    # Назначаем права администратора указанному пользователю
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    # Обновляем глобальную переменную
    _ADMIN_ID = user_id


def remove_admin_id():
    """
    Убирает права администратора у всех пользователей
    Используется для сброса административных прав
    """
    global _ADMIN_ID
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Сбрасываем права администратора у всех пользователей
    cursor.execute("UPDATE users SET is_admin = 0")
    conn.commit()
    conn.close()

    # Обновляем глобальную переменную
    _ADMIN_ID = None


# Загружаем роли при импорте модуля
load_roles_from_db()
