import logging
import requests
import json
from config import redis_client
import uuid
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

CRM_URL = "http://web:8000/api/bid/"
from config import CRM_TOKEN
def create_bid_in_crm(url_users: str, other_fields: dict = None):
    payload = {
        "url_users": url_users,
    }
    headers = {
    "Authorization": f"Token {CRM_TOKEN}",
    "Content-Type": "application/json"
    }
    
    if other_fields:
        payload.update(other_fields)

    try:
        response = requests.post(CRM_URL, json=payload, timeout=10, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Создана заявка в CRM: {data.get('id')}")
        return data
    except Exception as e:
        logger.error(f"Ошибка при создании заявки в CRM: {e}")
        return None

async def push_notification_to_redis(event: dict):
    if "id" not in event:
        event["id"] = str(uuid.uuid4())
    if "read" not in event:
        event["read"] = False
    await redis_client.rpush("notifications_queue", json.dumps(event))



async def wait_for_bid_details(bid_id, timeout=10):
    """
    Ждём, пока Celery обновит заявку в CRM.
    """
    headers = {
    "Authorization": f"Token {CRM_TOKEN}",
    "Content-Type": "application/json"
    }
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f"{CRM_URL}{bid_id}/") as resp:
                    data = await resp.json()
                    if data.get("brand") and data.get("model"):
                        return data
        except Exception as e:
            logger.error(f"Ошибка при получении данных заявки {bid_id}: {e}")
        await asyncio.sleep(1)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{CRM_URL}{bid_id}/") as resp:
            return await resp.json()
        


async def update_bid_topics(bid_id: int, thread_id: int) -> bool:
    """
    Обновляет заявку, записывая в неё айди темы (форумного топика).
    """
    url = f"{CRM_URL}{bid_id}/update/"
    headers = {
        "Authorization": f"Token {CRM_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"thread_id": thread_id}
    try:
        response = requests.patch(url, json=payload, timeout=10, headers=headers)
        response.raise_for_status()
        logger.info(f"Заявка {bid_id} обновлена, topic_id={thread_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении заявки {bid_id}: {e}")
        return False
