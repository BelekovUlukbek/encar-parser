import os
import uuid
import hashlib
from datetime import datetime, timedelta

# Импортируем db и User внутри функций чтобы избежать circular import
# from src.user_database import db, User  ← делается внутри функций

# ============================================================
#  НАСТРОЙКИ — заполни в .env
# ============================================================
MBANK_NUMBER    = os.environ.get('MBANK_NUMBER',    '+996 XXX XXX XXX')
ODENGI_NUMBER   = os.environ.get('ODENGI_NUMBER',   '+996 XXX XXX XXX')
ADMIN_WHATSAPP  = os.environ.get('ADMIN_WHATSAPP',  '+996 XXX XXX XXX')
ADMIN_TELEGRAM  = os.environ.get('ADMIN_TELEGRAM',  '@your_telegram')

# Freedom Pay (заполни когда получишь ключи)
FREEDOM_PAY_KEY         = os.environ.get('FREEDOM_PAY_KEY', '')
FREEDOM_PAY_SECRET      = os.environ.get('FREEDOM_PAY_SECRET', '')
FREEDOM_PAY_MERCHANT_ID = os.environ.get('FREEDOM_PAY_MERCHANT_ID', '')

# ============================================================
#  ТАРИФЫ — сколько дней и поисков даёт каждый план
# ============================================================
PLAN_DAYS = {
    '1':        3,
    '5':        3,
    '50':       3,
    'search7':  7,
    'search14': 14,
    'search30': 30,
}

PLAN_SEARCHES = {
    '1':        1,
    '5':        5,
    '50':       50,
    'search7':  9999,
    'search14': 9999,
    'search30': 9999,
}

# ============================================================
#  ВСПОМОГАТЕЛЬНОЕ
# ============================================================
def generate_payment_id(user_id: int) -> str:
    """Генерирует читаемый уникальный ID платежа: AK-0042-A1B2"""
    suffix = str(uuid.uuid4())[:4].upper()
    return f"AK-{user_id:04d}-{suffix}"


# ============================================================
#  РУЧНАЯ ОПЛАТА (Mbank / О!Деньги)
# ============================================================
def create_manual_payment_instruction(plan: str,
                                      price: int,
                                      plan_name: str,
                                      user_id: int,
                                      username: str) -> dict:
    """
    Возвращает словарь с инструкцией по ручной оплате.
    Этот словарь передаётся в шаблон payment.html
    """
    payment_id = generate_payment_id(user_id)

    days     = PLAN_DAYS.get(plan, 3)
    searches = PLAN_SEARCHES.get(plan, 1)
    searches_label = f"{searches} поисков" if searches < 9000 else "Безлимитные поиски"

    whatsapp_url = (
        f"https://wa.me/{ADMIN_WHATSAPP.replace(' ', '').replace('+', '')}"
        f"?text=Оплата%20{payment_id}%20-%20{username}"
    )
    telegram_url = f"https://t.me/{ADMIN_TELEGRAM.lstrip('@')}"

    return {
        "payment_id":     payment_id,
        "amount":         price,
        "plan":           plan,
        "plan_name":      plan_name,
        "days":           days,
        "searches_label": searches_label,

        # Реквизиты
        "mbank_number":   MBANK_NUMBER,
        "odengi_number":  ODENGI_NUMBER,

        # Ссылки для связи
        "whatsapp_url":   whatsapp_url,
        "telegram_url":   telegram_url,
        "admin_telegram": ADMIN_TELEGRAM,
        "admin_whatsapp": ADMIN_WHATSAPP,

        # Пошаговая инструкция
        "steps": [
            {
                "num": 1,
                "icon": "💳",
                "title": "Переведите деньги",
                "text": (
                    f"Mbank или О!Деньги: переведите <strong>{price} сом</strong> "
                    f"на номер <strong>{MBANK_NUMBER}</strong>"
                ),
            },
            {
                "num": 2,
                "icon": "💬",
                "title": "Укажите код в комментарии",
                "text": (
                    f"В комментарии к переводу напишите: "
                    f"<strong>{payment_id}</strong>"
                ),
            },
            {
                "num": 3,
                "icon": "📸",
                "title": "Отправьте скриншот",
                "text": (
                    f"Скиньте скриншот оплаты нам в "
                    f"<a href='{whatsapp_url}' target='_blank'>WhatsApp</a> или "
                    f"<a href='{telegram_url}' target='_blank'>Telegram</a>"
                ),
            },
            {
                "num": 4,
                "icon": "⚡",
                "title": "Активация тарифа",
                "text": "Активируем тариф в течение <strong>1–2 часов</strong> (пн–вс 09:00–22:00)",
            },
        ],
    }


# ============================================================
#  АКТИВАЦИЯ ТАРИФА АДМИНИСТРАТОРОМ
# ============================================================
def activate_plan_manual(user_id: int, plan: str) -> bool:
    """
    Активирует тариф пользователю.
    Вызывается из /admin/activate после проверки оплаты.
    """
    from src.user_database import db, User

    user = User.query.get(user_id)
    if not user:
        return False

    days     = PLAN_DAYS.get(plan, 3)
    searches = PLAN_SEARCHES.get(plan, 1)

    user.is_premium      = True
    user.premium_until   = datetime.now() + timedelta(days=days)
    user.searches_left   = searches
    user.searches_count  = 0       # сбрасываем бесплатный счётчик

    db.session.commit()
    print(f"✅ Тариф '{plan}' активирован для {user.username} до {user.premium_until:%d.%m.%Y}")
    return True


# ============================================================
#  FREEDOM PAY — ЗАГОТОВКА
#  Раскомментируй и используй после получения ключей
# ============================================================
#
# import requests
#
# def create_freedompay_order(plan: str,
#                             price: int,
#                             plan_name: str,
#                             user_id: int,
#                             base_url: str) -> str | None:
#     """
#     Создаёт платёж в Freedom Pay и возвращает ссылку для редиректа.
#     base_url — адрес твоего сайта, например 'https://autokorea.kg'
#     """
#     import uuid
#
#     order_id = generate_payment_id(user_id)
#     salt     = str(uuid.uuid4())[:8]
#
#     payload = {
#         "pg_merchant_id":  FREEDOM_PAY_MERCHANT_ID,
#         "pg_order_id":     order_id,
#         "pg_amount":       str(price),
#         "pg_currency":     "KGS",
#         "pg_description":  plan_name,
#         "pg_success_url":  f"{base_url}/payment/success",
#         "pg_failure_url":  f"{base_url}/payment/failure",
#         "pg_user_id":      str(user_id),
#         "pg_salt":         salt,
#     }
#
#     # Формируем подпись
#     values = [str(v) for v in sorted(payload.values())]
#     sign_string = "init_payment.php;" + ";".join(values) + ";" + FREEDOM_PAY_SECRET
#     payload["pg_sig"] = hashlib.md5(sign_string.encode()).hexdigest()
#
#     resp = requests.post(
#         "https://api.freedompay.kg/init_payment.php",
#         data=payload,
#         timeout=10
#     )
#     result = resp.json()
#
#     if result.get("pg_status") == "ok":
#         return result.get("pg_redirect_url")
#
#     print(f"❌ Freedom Pay ошибка: {result}")
#     return None
#
#
# @app.route('/payment/success')
# @login_required
# def payment_success():
#     """Freedom Pay редиректит сюда после успешной оплаты"""
#     # Верификация подписи + активация тарифа
#     order_id = request.args.get('pg_order_id')
#     # ... верификация ...
#     flash('🎉 Оплата прошла успешно! Тариф активирован.', 'success')
#     return redirect(url_for('profile'))
#
#
# @app.route('/payment/failure')
# def payment_failure():
#     """Freedom Pay редиректит сюда при отказе"""
#     flash('❌ Оплата не прошла. Попробуйте снова.', 'danger')
#     return redirect(url_for('pricing'))