import sqlite3
from datetime import datetime, timedelta
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import asyncpg
import asyncio


def dict_factory(cursor, row):
    """
    Фабрика для создания словарей из результатов SQL запросов
    
    Преобразует строки БД в словари с названиями колонок как ключами
    
    Args:
        cursor: Курсор SQLite
        row: Строка результата запроса
        
    Returns:
        Словарь с данными строки
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def get_db_connection():
    """
    Создает и возвращает соединение с базой данных
    
    Настраивает фабрику словарей для удобной работы с результатами
    
    Returns:
        Соединение с SQLite базой данных
    """
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.row_factory = dict_factory
    return conn

#берем все заказы менеджера

def get_my_orders(manager_id: int):
    """
    Получает все заказы указанного пользователя
    
    Args:
        manager_id: ID пользователя
        
    Returns:
        Список заказов компании
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE manager_id = ?", (manager_id,)
        ).fetchall()
    
#взять компанию
def get_company_info(company_id: int):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()

    if row:
        return dict(row)
    return None
    

#берем все данные заказа
def get_order_by_id(id: int):
    """
    Получает данные заказа по id
    
    Args:
        id: ID пользователя
        
    Returns:
        Данные заказа
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM bid WHERE id = ?", (id,)
        ).fetchone()

    if row:
        return dict(row)
    return None


#Обновляем авто в наличии

def mark_order_in_stock(order_id: int):
    """Проставляет флаг in_stock=True для заявки"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE bid SET in_stock = 1 WHERE id = ?",
            (order_id,)
        )
        conn.commit()


#Обновляем дилера
def dealer_info_update(company_name: str, dealer_photo: str, order_id: int):
    """Обновление данных о дилере"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE dealers SET company_name = ?, photo = ? WHERE id = ?",
            (company_name, dealer_photo, order_id)
        )
        conn.commit()

#Проверяем дилера в наличии
def dealer_info_find(company_name: str, dealer_photo: str, order_id: int):
    """Поиск данных о дилере"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
                "SELECT id FROM dealers WHERE company_name = ? AND photo = ? AND id = ?",
                (company_name, dealer_photo, order_id)
            )
        row = cursor.fetchone()
        return row

#Создаем дилера
def dealer_info_create(company_name: str, dealer_photo: str, order_id: int):
    """Создаём дилера и привязываем к заявке"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # создаём дилера (id автоинкремент)
        cursor.execute(
            "INSERT INTO dealers (company_name, photo) VALUES (?, ?)",
            (company_name, dealer_photo)
        )
        dealer_id = cursor.lastrowid
        cursor.execute(
            "UPDATE bid SET dealer_id = ? WHERE id = ?",
            (dealer_id, order_id)
        )
        conn.commit()

def get_rings_orders():
    """
    Получает заказы со статусом прозвоны
        
    Returns:
        Список старых открытых заказов
    """
    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM bid
            WHERE status = 'ring' and dealer_id is NULL
            """,
        ).fetchall()
    

def get_company_by_id(company_id: int):
    """
    Получает информацию о компании по ID
    
    Args:
        company_id: ID компании
        
    Returns:
        Словарь с данными компании или None если не найдена
    """
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()



def get_thread_calls(tg_id: int) -> int | None:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT calls_id FROM groups WHERE tg_id = ?",
            (tg_id,)
        ).fetchone()
        if row:
            return row["calls_id"]
        return None
    

def mark_order_as_shown_to_caller(order_id: int):
    """Проставляет флаг caller_saw=True для заявки"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE bid SET caller_saw = 1 WHERE id = ?",
            (order_id,)
        )
        conn.commit()


#вОЗВРАЩАЕМ СТАТУС В DISABLE
def status_disable(order_id: int):
    """Обновление данных о статусе"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE bid SET status = 'disable' WHERE id = ?",
            (order_id)
        )
        conn.commit()