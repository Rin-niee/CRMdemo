import requests
import random
import time
from urllib.parse import urlparse, parse_qs
from celery import shared_task
from django.db import transaction
from demo.models import bid
import logging
logger = logging.getLogger(__name__)

def parse_car_data(raw_car):
    fuels = {
        "디젤": "Дизель",
        "가솔린": "Бензин",
        "가솔린+전기": "Гибрид",
        "전기": "Электро",
    }

    transmissions = {
        "오토": "Автомат",
        "수동": "Механика",
    }

    return {
        "brand": raw_car.get("manufacturerNm"),
        "model": raw_car.get("modelNm"),
        "year": raw_car.get("formYear"),
        "engine": str(round(raw_car.get("displacement", 0) / 1000, 2)) if raw_car.get("displacement") else None,
        "fuel_type": fuels.get(raw_car.get("fuelNm"), raw_car.get("fuelNm")),
        "mileage": raw_car.get("mileage"),
        "transmission": transmissions.get(raw_car.get("transmission"), raw_car.get("transmission")),
    }

@shared_task
def fetch_car_data_task(bid_id, car_urls):
    logger.info(f"🚀 Запустили задачу для bid_id={bid_id}, urls={car_urls}")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://buy.encar.com/",
        "Origin": "https://buy.encar.com",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        bid_instance = bid.objects.get(id=bid_id)
    except bid.DoesNotExist:
        print(f"❌ Заявка с id={bid_id} не найдена")
        return

    for url in car_urls:
        logger.info(f"🔗 Работаем с URL: {url}")
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            carid_list = params.get("carid")
            logger.info(f":() Не удалось извлечь: {carid_list}")
            if not carid_list:
                print(f"❌ Не удалось извлечь carId из {url}")
                continue
            carid = carid_list[0]

            api_url = f"https://api.encar.com/legacy/usedcar/sale/car?carIds={carid}"
            resp = requests.get(api_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, list) and data:
                parsed_car = parse_car_data(data[0])
                logger.info(f"Информация: {parsed_car}")
                with transaction.atomic():
                    bid_instance.brand = parsed_car.get("brand")
                    bid_instance.model = parsed_car.get("model")
                    bid_instance.year = parsed_car.get("year")
                    bid_instance.engine = parsed_car.get("engine")
                    bid_instance.fuel_type = parsed_car.get("fuel_type")
                    bid_instance.mileage = parsed_car.get("mileage")
                    bid_instance.transmission = parsed_car.get("transmission")
                    bid_instance.url = url
                    bid_instance.save()
                    print(f"✅ Заявка {bid_id} обновлена с carId={carid}")
            else:
                print(f"⚠️ Пустой ответ API по carId={carid}")
        except Exception as e:
            print(f"❌ Ошибка при обработке {url}: {e}")

        time.sleep(random.uniform(1, 3))
