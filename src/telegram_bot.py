# src/telegram_bot.py
import os
import requests

TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def send_message(text: str) -> bool:
    """Отправляет сообщение в Telegram. Возвращает True если успешно."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram не настроен (нет токена или chat_id)")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False


def notify_payment(payment_id: str, username: str, plan_name: str, price: int) -> bool:
    """Уведомление о новой заявке на оплату."""
    text = (
        f"💰 <b>Новая заявка об оплате!</b>\n\n"
        f"👤 Пользователь: <b>{username}</b>\n"
        f"📋 Тариф: <b>{plan_name}</b>\n"
        f"💵 Сумма: <b>{price} сом</b>\n"
        f"🔑 Код платежа: <code>{payment_id}</code>\n\n"
        f"✅ Проверь перевод и активируй тариф в админ-панели."
    )
    return send_message(text)


def notify_new_user(username: str, email: str) -> bool:
    """Уведомление о новой регистрации."""
    text = (
        f"🆕 <b>Новый пользователь!</b>\n\n"
        f"👤 Имя: <b>{username}</b>\n"
        f"📧 Email: <b>{email}</b>"
    )
    return send_message(text)