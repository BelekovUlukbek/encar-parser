# src/auto_api_client.py
import requests
import base64
import os
from typing import Optional

AUTO_API_LOGIN = os.environ.get('AUTO_API_LOGIN', '')      # твой логин от auto-api.com
AUTO_API_PASSWORD = os.environ.get('AUTO_API_PASSWORD', '') # твой пароль
AUTO_API_ACCESS_NAME = os.environ.get('AUTO_API_ACCESS_NAME', '') # например: "myaccount"

def _get_auth_header():
    credentials = f"{AUTO_API_LOGIN}:{AUTO_API_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def search_by_vin_api(vin: str) -> Optional[dict]:
    """
    Ищет автомобиль по VIN через auto-api.com
    Возвращает словарь с данными или None если не найден
    """
    if not AUTO_API_LOGIN:
        # Если ключа нет — возвращаем None, сайт сам скажет пользователю
        return None

    try:
        # auto-api.com позволяет фильтровать по VIN через их endpoint
        url = f"https://{AUTO_API_ACCESS_NAME}.auto-api.com/search"
        params = {"vin": vin, "limit": 1}
        headers = _get_auth_header()

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("result", [])
        if not results:
            return None

        car_raw = results[0].get("data", results[0])
        return _normalize_car(car_raw)

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка auto-api.com: {e}")
        return None

def _normalize_car(raw: dict) -> dict:
    """Приводит ответ auto-api.com к формату нашей БД"""
    extra = raw.get("extra", {})
    accidents = extra.get("accidents", [])

    return {
        "vehicle_id": raw.get("inner_id"),
        "vin": raw.get("vin", ""),
        "manufacturer": raw.get("mark", ""),
        "manufacturer_ko": raw.get("mark", ""),
        "model": raw.get("model", ""),
        "model_ko": raw.get("model", ""),
        "year": raw.get("year"),
        "price": raw.get("price_won"),
        "price_usd": raw.get("price"),
        "mileage": raw.get("km_age"),
        "fuel_type": raw.get("engine_type", ""),
        "transmission": raw.get("transmission_type", ""),
        "color": raw.get("color", ""),
        "engine_capacity": raw.get("displacement", ""),
        "body_type": raw.get("body_type", ""),
        "images": raw.get("images", []),
        "original_url": raw.get("url", ""),
        "address": raw.get("address", ""),
        "accidents_count": len(accidents),
        "accidents": accidents,
        "diagnosis": extra.get("diagnosis", {}),
        "inspection": extra.get("inspection", {}),
        "is_dealer": raw.get("is_dealer", False),
    }