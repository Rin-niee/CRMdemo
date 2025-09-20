import sqlite3
from datetime import datetime, timedelta
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import asyncpg
import asyncio

async def get_db_connection():
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn


async def get_companies():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT id, name FROM companies")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_bids():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT id, thread_id FROM bids where thread_id is not NULL")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_bid_by_thread_id(thread_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id FROM bid WHERE thread_id = $1",
            thread_id
        )
        return dict(row) if row else None
    finally:
        await conn.close()


async def get_orders_by_company(company_id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE company_id = $1", company_id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()
    

async def get_thread_information(tg_id: int) -> int | None:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT inspection_id FROM groups WHERE tg_id = $1", tg_id
        )
        return row["inspection_id"] if row else None
    finally:
        await conn.close()
    
async def get_thread_clients(tg_id: int) -> int | None:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT clients_id FROM groups WHERE tg_id = $1", tg_id
        )
        return row["clients_id"] if row else None
    finally:
        await conn.close()

async def get_all_users(manager_id: int) -> int | None:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT group_id FROM users WHERE id = $1 LIMIT 1", manager_id
        )
        return row["group_id"] if row else None
    finally:
        await conn.close()

async def get_manager_group(id: int) -> int | None:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT tg_id FROM groups WHERE id = $1 LIMIT 1", id
        )
        return row["tg_id"] if row else None
    finally:
        await conn.close()

async def get_my_order(id: int) -> int | None:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT count(id) as cnt FROM bid WHERE status = 'open' AND manager_id = $1", id
        )
        return row["cnt"] if row else None
    finally:
        await conn.close()

async def get_order_by_id(order_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM bid WHERE id = $1", order_id
        )
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_all_orders_by_status(statuses: list):
    conn = await get_db_connection()
    try:
        placeholders = ','.join(f"${i+1}" for i in range(len(statuses)))
        rows = await conn.fetch(
            f"SELECT * FROM bid WHERE status IN ({placeholders})", *statuses
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_orders_by_status(user_id: int, statuses: list):
    conn = await get_db_connection()
    try:
        placeholders = ','.join(f"${i+2}" for i in range(len(statuses)))
        query = f"SELECT * FROM bid WHERE manager_id = $1 AND status IN ({placeholders})"
        rows = await conn.fetch(query, user_id, *statuses)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def update_order_status(order_id: str, status: str):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE bid SET status = $1 WHERE id = $2", status, order_id
        )
    finally:
        await conn.close()

async def assign_manager_to_order(order_id: str, manager_id: int):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE bid SET manager_id = $1 WHERE id = $2", manager_id, order_id
        )
    finally:
        await conn.close()


async def clear_manager_for_order(order_id: str):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE bid SET manager_id = NULL WHERE id = $1", order_id
        )
    finally:
        await conn.close()

async def get_user_orders_by_single_status(user_id: int, status: str):
    return await get_orders_by_status(user_id, [status])

async def get_all_user_orders(user_id: int):
    all_statuses = ["open", "progress", "done"]
    return await get_orders_by_status(user_id, all_statuses)

async def get_all_open_orders():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM bid WHERE status = 'open'")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_all_orders_for_me(manager_id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE manager_id = $1", manager_id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_bid_info(id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE id = $1", id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_all_open_orders_for_me(manager_id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE status = 'open' AND manager_id = $1", manager_id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_orders_with_deadline():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM bid WHERE deadline IS NOT NULL")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_orders_with_opened_at():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE opened_at IS NOT NULL ORDER BY opened_at DESC"
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_open_orders_with_opened_at():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE status = 'open' AND manager_id IS NULL AND opened_at IS NOT NULL ORDER BY opened_at DESC"
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()
    
async def get_open_orders_with_opened_at_day():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE status = 'open' AND opened_at IS NOT NULL AND opened_at >= NOW() - INTERVAL '1 day' ORDER BY opened_at DESC"
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_available_orders_by_company(company_id: int, user_id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM bid
            WHERE company_id = $1
              AND (status = 'open' OR (manager_id = $2 AND status IN ('progress','review')))
            """,
            company_id, user_id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_companies_with_disabled_orders():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT DISTINCT c.id, c.name
            FROM companies c
            JOIN bid o ON o.company_id = c.id
            WHERE o.status = 'disabled'
            ORDER BY c.name
            """
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_disabled_orders_by_company(company_id: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM bid WHERE company_id = $1 AND status = 'disabled'",
            company_id
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_active_manager_ids():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT DISTINCT manager_id FROM bid WHERE manager_id IS NOT NULL AND status IN ('progress','review')"
        )
        return [row["manager_id"] for row in rows]
    finally:
        await conn.close()


async def get_progress_manager_ids():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT DISTINCT manager_id FROM bid WHERE manager_id IS NOT NULL AND status = 'progress'"
        )
        return [row["manager_id"] for row in rows]
    finally:
        await conn.close()


async def mark_order_open(order_id: str):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE bid SET status = 'open', opened_at = CURRENT_TIMESTAMP WHERE id = $1",
            order_id
        )
    finally:
        await conn.close()

async def get_open_orders_older_than(min_age_seconds: int):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT *
            FROM bid
            WHERE status = 'open'
              AND opened_at IS NOT NULL
              AND EXTRACT(EPOCH FROM (NOW() - opened_at)) >= $1
            ORDER BY opened_at ASC
            """,
            min_age_seconds
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_company_by_id(company_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM companies WHERE id = $1", company_id
        )
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_dealer_by_id(dealer_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM dealers WHERE id = $1", dealer_id
        )
        return dict(row) if row else None
    finally:
        await conn.close()

async def _exec(query: str, *params):
    conn = await get_db_connection()
    try:
        await conn.execute(query, *params)
    finally:
        await conn.close()

async def ensure_user_exists(user_id: int):
    await _exec(
        "INSERT INTO users(id, is_admin) VALUES($1, 0) ON CONFLICT (id) DO NOTHING",
        user_id
    )

async def set_checklist_answer(order_id: int, q_index: int, value: bool):
    col = "checklist_point1" if q_index == 1 else "checklist_point2"
    await _exec(f"UPDATE bid SET {col} = $1 WHERE id = $2", 1 if value else 0, order_id)


async def reset_checklist_answers(order_id: int):
    await _exec(
        "UPDATE bid SET checklist_point1 = NULL, checklist_point2 = NULL WHERE id = $1",
        order_id
    )

async def get_checklist_answers(order_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT checklist_point1, checklist_point2 FROM bid WHERE id = $1",
            order_id
        )
        if row:
            return dict(row)
        return {"checklist_point1": None, "checklist_point2": None}
    finally:
        await conn.close()

async def set_checklist_answer_text(order_id: int, q_index: int, value_code: str):
    col = "checklist_point1" if q_index == 1 else "checklist_point2"
    await _exec(f"UPDATE bid SET {col} = $1 WHERE id = $2", value_code, order_id)

async def save_arrival_time(order_id: int, arrival_time: datetime | None, manager_id: int, status: str):
    await _exec(
        "UPDATE bid SET arrived_time = $1, manager_id = $2, status = $3 WHERE id = $4",
        arrival_time, manager_id, status, order_id
    )
    return arrival_time

async def mark_order_as_shown(order_id: int):
    await _exec("UPDATE bid SET shown_to_bot = TRUE WHERE id = $1", order_id)

async def insert_file_record(bid_id: int, file_path: str):
    await _exec(
        "INSERT INTO photo (bid_id, file_url) VALUES ($1, $2)",
        bid_id, file_path
    )

async def get_photo_by_bid_id(bid_id: int):
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT file_url FROM photo WHERE bid_id = $1", bid_id)
    await conn.close()
    return [dict(row) for row in rows] if rows else []
