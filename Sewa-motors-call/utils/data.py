import asyncpg
from config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT
from datetime import datetime

async def get_db_connection():
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# 1. Взять компанию
async def get_company_info(company_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM companies WHERE id = $1", company_id)
    await conn.close()
    return dict(row) if row else None

# 2. Данные заказа по id
async def get_order_by_id(order_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM bid WHERE id = $1", order_id)
    await conn.close()
    return dict(row) if row else None

# 3. Проставляем авто в наличии
async def mark_order_in_stock(order_id: int):
    conn = await get_db_connection()
    await conn.execute("UPDATE bid SET in_stock = TRUE WHERE id = $1", order_id)
    await conn.close()

# 4. Привязка дилера к заявке
async def attach_dealer_to_bid(dealer_id: int, order_id: int):
    conn = await get_db_connection()
    await conn.execute("UPDATE bid SET dealer_id = $1 WHERE id = $2", dealer_id, order_id)
    await conn.close()

# 5. Проверяем дилера в наличии
async def dealer_info_find(company_name: str):
    conn = await get_db_connection()
    row = await conn.fetchrow(
        "SELECT id FROM dealers WHERE company_name = $1",
        company_name
    )
    await conn.close()
    return dict(row) if row else None

# 6. Создаем дилера
async def dealer_info_create(company_name: str, dealer_photo: str, order_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow(
        "INSERT INTO dealers (company_name, photo) VALUES ($1, $2) RETURNING id",
        company_name, dealer_photo
    )
    dealer_id = row["id"]
    await conn.execute("UPDATE bid SET dealer_id = $1 WHERE id = $2", dealer_id, order_id)
    await conn.close()
    return dealer_id

# 7. Заказы со статусом "ring"
async def get_rings_orders():
    conn = await get_db_connection()
    rows = await conn.fetch(
        "SELECT * FROM bid WHERE status = 'ring' AND dealer_id IS NULL"
    )
    await conn.close()
    return [dict(r) for r in rows]

# 8. Получаем компанию по id
async def get_company_by_id(company_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM companies WHERE id = $1", company_id)
    await conn.close()
    return dict(row) if row else None

# 9. Получаем calls_id по tg_id
async def get_thread_calls(tg_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT calls_id FROM groups WHERE tg_id = $1", tg_id)
    await conn.close()
    return row["calls_id"] if row else None

# 10. Проставляем caller_saw
async def mark_order_as_shown_to_caller(order_id: int):
    conn = await get_db_connection()
    await conn.execute("UPDATE bid SET caller_saw = TRUE WHERE id = $1", order_id)
    await conn.close()

# 11. Статус disable
async def status_disable(order_id: int):
    conn = await get_db_connection()
    await conn.execute("UPDATE bid SET status = 'disable' WHERE id = $1", order_id)
    await conn.close()


# 12. Взять все заказы
async def get_all_order():
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM bid WHERE status = 'ring'")
    await conn.close()
    return dict(row) if row else None