import sqlite3
from datetime import datetime, timedelta
DB_PATH = "db.sqlite3"


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


def get_db_connection():
    """
    Создает и возвращает соединение с базой данных
    
    Настраивает фабрику словарей для удобной работы с результатами
    
    Returns:
        Соединение с SQLite базой данных
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn


def get_companies():
    """
    Получает список всех компаний из базы данных
    
    Returns:
        Список словарей с информацией о компаниях (id, name)
    """
    with get_db_connection() as conn:
        return conn.execute("SELECT id, name FROM companies").fetchall()


def get_orders_by_company(company_id: int):
    """
    Получает все заказы для указанной компании
    
    Args:
        company_id: ID компании
        
    Returns:
        Список заказов компании
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE company_id = ?", (company_id,)
        ).fetchall()
    

def get_thread_information(tg_id: int) -> int | None:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT inspection_id FROM groups WHERE tg_id = ?",
            (tg_id,)
        ).fetchone()
        if row:
            return row["inspection_id"]
        return None
    
def get_thread_clients(tg_id: int) -> int | None:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT clients_id FROM groups WHERE tg_id = ?",
            (tg_id,)
        ).fetchone()
        if row:
            return row["clients_id"]
        return None

def get_all_users(manager_id: int) -> int | None:
    """
    Возвращает tg_id группы, в которой состоит менеджер
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT group_id FROM users WHERE id = ? LIMIT 1",
            (manager_id,)
        ).fetchone()
        return row["group_id"] if row else None

def get_manager_group(id: int) -> int | None:
    """
    Возвращает tg_id группы, в которой состоит менеджер
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT tg_id FROM groups WHERE id = ? LIMIT 1",
            (id,)
        ).fetchone()
        return row["tg_id"] if row else None

def get_my_order(id: int) -> int | None:
    """
    Возвращает tg_id группы, в которой состоит менеджер
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT count(id) as cnt FROM bid WHERE status = 'open' and manager_id = ?",
            (id,)
        ).fetchone()
        return row["cnt"] if row else None


def get_order_by_id(order_id: int):
    """
    Получает заказ по его ID
    
    Args:
        order_id: ID заказа
        
    Returns:
        Словарь с данными заказа или None если не найден
    """
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM bid WHERE id = ?", (order_id,)).fetchone()


def get_all_orders_by_status(statuses: list):
    """
    Получает все заказы с указанными статусами
    
    Args:
        statuses: Список статусов для фильтрации
        
    Returns:
        Список заказов с указанными статусами
    """
    placeholders = ",".join(["?"] * len(statuses))
    with get_db_connection() as conn:
        return conn.execute(
            f"SELECT * FROM bid WHERE status IN ({placeholders})", statuses
        ).fetchall()


def get_orders_by_status(user_id: int, statuses: list):
    """
    Получает заказы пользователя с указанными статусами
    
    Args:
        user_id: ID пользователя (менеджера)
        statuses: Список статусов для фильтрации
        
    Returns:
        Список заказов пользователя с указанными статусами
    """
    placeholders = ",".join(["?"] * len(statuses))
    with get_db_connection() as conn:
        return conn.execute(
            f"SELECT * FROM bid WHERE manager_id = ? AND status IN ({placeholders})",
            [user_id] + statuses,
        ).fetchall()


def update_order_status(order_id: str, status: str):
    """
    Обновляет статус заказа
    
    Args:
        order_id: ID заказа для обновления
        status: Новый статус заказа
    """
    with get_db_connection() as conn:
        conn.execute("UPDATE bid SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()


def assign_manager_to_order(order_id: str, manager_id: int):
    """
    Назначает менеджера к заказу
    
    Привязывает заказ к конкретному исполнителю
    
    Args:
        order_id: ID заказа
        manager_id: ID менеджера/исполнителя
    """
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE bid SET manager_id = ? WHERE id = ?", (manager_id, order_id)
        )
        conn.commit()


def clear_manager_for_order(order_id: str):
    """
    Убирает назначенного менеджера с заказа
    
    Освобождает заказ от исполнителя
    
    Args:
        order_id: ID заказа
    """
    with get_db_connection() as conn:
        conn.execute("UPDATE bid SET manager_id = NULL WHERE id = ?", (order_id,))
        conn.commit()


def get_user_orders_by_single_status(user_id: int, status: str):
    """
    Получает заказы пользователя с одним конкретным статусом
    
    Args:
        user_id: ID пользователя
        status: Статус заказов
        
    Returns:
        Список заказов пользователя с указанным статусом
    """
    return get_orders_by_status(user_id, [status])


def get_all_user_orders(user_id: int):
    """
    Получает все заказы пользователя (открытые, в работе, завершенные)
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Список всех заказов пользователя
    """
    all_statuses = ["open", "progress", "done"]
    return get_orders_by_status(user_id, all_statuses)


def get_all_open_orders():
    """
    Получает все открытые заказы (статус 'open')
    
    Returns:
        Список всех открытых заказов
    """
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM bid WHERE status = 'open'").fetchall()


def get_orders_with_deadline():
    """
    Получает заказы, у которых установлен дедлайн
    
    Returns:
        Список заказов с дедлайном
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE deadline IS NOT NULL"
        ).fetchall()


def get_orders_with_opened_at():
    """
    Получает заказы, у которых установлено время открытия
    
    Сортирует по времени открытия (новые сначала)
    
    Returns:
        Список заказов с временем открытия, отсортированный по убыванию
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE opened_at IS NOT NULL ORDER BY opened_at DESC"
        ).fetchall()


def get_open_orders_with_opened_at():
    """
    Получает открытые заказы с временем открытия
    
    Возвращает заказы со статусом 'open' и установленным временем открытия
    
    Returns:
        Список открытых заказов с временем открытия
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE status = 'open' AND opened_at IS NOT NULL ORDER BY opened_at DESC"
        ).fetchall()
    

def get_open_orders_with_opened_at_day():
    """
    Получает открытые заказы с временем открытия
    
    Возвращает заказы со статусом 'open' и установленным временем открытия
    
    Returns:
        Список открытых заказов с временем открытия
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE status = 'open' AND opened_at IS NOT NULL  AND opened_at >= datetime('now', '-1 day') ORDER BY opened_at DESC"
        ).fetchall()


def get_available_orders_by_company(company_id: int, user_id: int):
    """
    Получает доступные заказы компании для пользователя
    
    Включает:
    - Открытые заказы (статус 'open')
    - Заказы пользователя в работе или на проверке
    
    Args:
        company_id: ID компании
        user_id: ID пользователя
        
    Returns:
        Список доступных заказов для пользователя
    """
    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM bid
            WHERE company_id = ?
              AND (
                    status = 'open'
                 OR (manager_id = ? AND status IN ('progress','review'))
              )
            """,
            (company_id, user_id),
        ).fetchall()


def get_companies_with_disabled_orders():
    """
    Получает компании, у которых есть отключенные заказы
    
    Returns:
        Список компаний с отключенными заказами
    """
    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT DISTINCT c.id, c.name
            FROM companies c
            JOIN bid o ON o.company_id = c.id
            WHERE o.status = 'disabled'
            ORDER BY c.name
            """
        ).fetchall()


def get_disabled_orders_by_company(company_id: int):
    """
    Получает отключенные заказы для указанной компании
    
    Args:
        company_id: ID компании
        
    Returns:
        Список отключенных заказов компании
    """
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM bid WHERE company_id = ? AND status = 'disabled'",
            (company_id,),
        ).fetchall()


def get_active_manager_ids():
    """
    Получает ID всех активных менеджеров
    
    Активными считаются менеджеры, у которых есть заказы в работе или на проверке
    
    Returns:
        Список ID активных менеджеров
    """
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT manager_id FROM bid
            WHERE manager_id IS NOT NULL AND status IN ('progress','review')
            """
        ).fetchall()
    return [r["manager_id"] if isinstance(r, dict) else r[0] for r in rows]


def get_progress_manager_ids():
    """
    Получает ID менеджеров, у которых есть заказы в работе
    
    Returns:
        Список ID менеджеров с заказами в статусе 'progress'
    """
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT manager_id FROM bid
            WHERE manager_id IS NOT NULL AND status = 'progress'
            """
        ).fetchall()
    return [r["manager_id"] if isinstance(r, dict) else r[0] for r in rows]


def mark_order_open(order_id: str):
    """
    Отмечает заказ как открытый
    
    Устанавливает статус 'open' и время открытия
    
    Args:
        order_id: ID заказа для открытия
    """
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE bid SET status = 'open', opened_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order_id,),
        )
        conn.commit()


def get_open_orders_older_than(min_age_seconds: int):
    """
    Получает открытые заказы старше указанного времени
    
    Args:
        min_age_seconds: Минимальный возраст заказа в секундах
        
    Returns:
        Список старых открытых заказов
    """
    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM bid
            WHERE status = 'open'
              AND opened_at IS NOT NULL
              AND (julianday('now') - julianday(opened_at)) * 86400 >= ?
            ORDER BY opened_at ASC
            """,
            (min_age_seconds,),
        ).fetchall()


# import aiosqlite

# async def get_open_orders_older_than_async(min_age_seconds: int):
#     """
#     Получает открытые заказы старше указанного времени (асинхронно)
#     """
#     async with aiosqlite.connect("your_db.sqlite") as db:
#         db.row_factory = aiosqlite.Row  # чтобы можно было обращаться как к словарю
#         async with db.execute(
#             """
#             SELECT *
#             FROM bid
#             WHERE status = 'open'
#               AND opened_at IS NOT NULL
#               AND (julianday('now') - julianday(opened_at)) * 86400 >= ?
#             ORDER BY opened_at ASC
#             """,
#             (min_age_seconds,)
#         ) as cursor:
#             rows = await cursor.fetchall()
#     return rows


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


def get_dealer_by_id(dealer_id: int):
    """
    Получает информацию о дилере по ID
    
    Args:
        dealer_id: ID дилера
        
    Returns:
        Словарь с данными дилера или None если не найден
    """
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM dealers WHERE id = ?", (dealer_id,)).fetchone()


def _exec(query: str, params: tuple = ()):
    """
    Вспомогательная функция для выполнения SQL запросов
    
    Args:
        query: SQL запрос
        params: Параметры для запроса
    """
    with get_db_connection() as conn:
        conn.execute(query, params)
        conn.commit()


def ensure_user_exists(user_id: int):
    """
    Создает запись пользователя в БД если её нет
    
    Использует INSERT OR IGNORE для избежания дублирования
    
    Args:
        user_id: ID пользователя для создания
    """
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users(id, is_admin) VALUES(?, 0)", (user_id,)
        )
        conn.commit()


def set_checklist_answer(order_id: int, q_index: int, value: bool):
    """
    Устанавливает ответ на вопрос чек-листа
    
    Args:
        order_id: ID заказа
        q_index: Индекс вопроса (1 или 2)
        value: Ответ (True/False)
    """
    col = "checklist_point1" if q_index == 1 else "checklist_point2"
    _exec(f"UPDATE bid SET {col} = ? WHERE id = ?", (1 if value else 0, order_id))


def reset_checklist_answers(order_id: int):
    """
    Сбрасывает все ответы чек-листа для заказа
    
    Args:
        order_id: ID заказа
    """
    _exec(
        "UPDATE bid SET checklist_point1 = NULL, checklist_point2 = NULL WHERE id = ?",
        (order_id,),
    )


def get_checklist_answers(order_id: int):
    """
    Получает ответы чек-листа для заказа
    
    Args:
        order_id: ID заказа
        
    Returns:
        Словарь с ответами чек-листа
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT checklist_point1, checklist_point2 FROM bid WHERE id = ?",
            (order_id,),
        ).fetchone()
    return row or {"checklist_point1": None, "checklist_point2": None}


def set_checklist_answer_text(order_id: int, q_index: int, value_code: str):
    """
    Устанавливает текстовый ответ на вопрос чек-листа
    
    Args:
        order_id: ID заказа
        q_index: Индекс вопроса (1 или 2)
        value_code: Текстовый код ответа
    """
    col = "checklist_point1" if q_index == 1 else "checklist_point2"
    _exec(f"UPDATE bid SET {col} = ? WHERE id = ?", (value_code, order_id))

def save_arrival_time(order_id: int, arrival_time: datetime, manager_id: int, status: str):
    arrival_time_str = arrival_time.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE bid SET arrived_time = ?, manager_id = ?, status = ? WHERE id = ?",
            (arrival_time_str, manager_id, status, order_id)
        )
        conn.commit()
    return arrival_time


def mark_order_as_shown(order_id: int):
    """Проставляет флаг shown_to_bot=True для заявки"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE bid SET shown_to_bot = 1 WHERE id = ?",
            (order_id,)
        )
        conn.commit()


def insert_file_record(bid_id: int, file_path: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO photo (bid_id, file_url)
            VALUES (?, ?)
            """,
            (bid_id, file_path)
        )

    conn.commit()
    conn.close()
