from src.telegram_bot import notify_payment, notify_new_user
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

load_dotenv()

from src.user_database import db, User, SearchHistory
from src.database import get_connection, search_by_vin, get_recent_cars, save_car
from src.auto_api_client import search_by_vin_api
from src.payment import (
    create_manual_payment_instruction,
    activate_plan_manual,
    PLAN_SEARCHES,
    PLAN_DAYS
)

# ============================================================
#  ПРИЛОЖЕНИЕ
# ============================================================
app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production-123456')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '🔐 Пожалуйста, войдите для доступа'
login_manager.login_message_category = 'warning'

# ============================================================
#  ТАРИФЫ
# ============================================================
PRICES = {
    '1':        450,
    '5':        1490,
    '50':       5400,
    'search7':  300,
    'search14': 500,
    'search30': 700,
}

PLAN_NAMES = {
    '1':        '1 отчёт — 3 дня доступа',
    '5':        '5 отчётов — 3 дня доступа',
    '50':       '50 отчётов — 3 дня доступа',
    'search7':  'Поиск Авто — 7 дней',
    'search14': 'Поиск Авто — 14 дней',
    'search30': 'Поиск Авто — 30 дней',
}

FREE_SEARCHES_LIMIT = 3

# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_searches_left(user):
    """Сколько поисков осталось у пользователя"""
    if not user.is_authenticated:
        return 0
    if user.is_premium:
        # Если премиум истёк — сбрасываем
        if user.premium_until and user.premium_until < datetime.now():
            user.is_premium = False
            user.searches_left = 0
            db.session.commit()
            return 0
        return user.searches_left if user.searches_left is not None else 999
    return max(0, FREE_SEARCHES_LIMIT - user.searches_count)


def normalize_car_images(car: dict) -> dict:
    """Парсим JSON-строку с изображениями в список"""
    if car.get('images') and isinstance(car['images'], str):
        try:
            car['images'] = json.loads(car['images'])
        except Exception:
            car['images'] = []
    return car


# ============================================================
#  СОЗДАНИЕ ТАБЛИЦ
# ============================================================
with app.app_context():
    db.create_all()
    print("✅ База данных пользователей готова")


# ============================================================
#  ПУБЛИЧНЫЕ СТРАНИЦЫ
# ============================================================
@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cars")
    total_cars = cursor.fetchone()[0]
    conn.close()

    recent = get_recent_cars(6)
    recent_list = [normalize_car_images(dict(r)) for r in recent]

    searches_left = get_searches_left(current_user) if current_user.is_authenticated else FREE_SEARCHES_LIMIT

    return render_template('index.html',
                           stats={'total_cars': total_cars, 'last_update': 'сегодня'},
                           recent_cars=recent_list,
                           searches_left=searches_left)


@app.route('/pricing')
def pricing():
    return render_template('pricing.html', prices=PRICES, plan_names=PLAN_NAMES)


# ============================================================
#  ПОИСК ПО VIN
# ============================================================
@app.route('/search')
def search():
    vin_query = request.args.get('vin', '').strip().upper()

    if not current_user.is_authenticated:
        flash('🔐 Войдите, чтобы искать автомобили', 'warning')
        return redirect(url_for('login'))

    searches_left = get_searches_left(current_user)

    if searches_left <= 0:
        flash('❌ Лимит поисков исчерпан. Оформите тариф!', 'danger')
        return redirect(url_for('pricing'))

    if not vin_query:
        flash('❌ Введите VIN номер', 'warning')
        return redirect(url_for('index'))

    if len(vin_query) < 5:
        flash('❌ VIN слишком короткий (минимум 5 символов)', 'warning')
        return redirect(url_for('index'))

    cars = []
    source = "local"

    # 1. Ищем в локальной БД (кэш)
    results = search_by_vin(vin_query)
    if results:
        cars = [normalize_car_images(dict(r)) for r in results]
    else:
        # 2. Запрашиваем auto-api.com
        api_result = search_by_vin_api(vin_query)
        if api_result:
            save_car(api_result)           # кэшируем в локальной БД
            cars = [api_result]
            source = "api"

    # Списываем поиск и пишем в историю
    history_entry = SearchHistory(user_id=current_user.id, vin=vin_query)
    db.session.add(history_entry)

    if current_user.is_premium:
        if current_user.searches_left and current_user.searches_left > 0:
            current_user.searches_left -= 1
    else:
        current_user.searches_count += 1

    db.session.commit()

    searches_left_after = get_searches_left(current_user)

    return render_template('search.html',
                           cars=cars,
                           query=vin_query,
                           searches_left=searches_left_after,
                           source=source,
                           found=len(cars) > 0)


# ============================================================
#  АВТОРИЗАЦИЯ
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('❌ Все поля обязательны', 'danger')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('❌ Имя пользователя минимум 3 символа', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('❌ Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('❌ Пароль минимум 6 символов', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('❌ Имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('❌ Email уже зарегистрирован', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # 🔔 Уведомление в Telegram
        notify_new_user(username, email)

        flash('✅ Регистрация прошла успешно! Войдите в аккаунт', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('❌ Неверное имя или пароль', 'danger')
            return redirect(url_for('login'))

        # Сбрасываем дневной счётчик при входе
        user.searches_count = 0
        db.session.commit()

        login_user(user, remember=remember)
        flash(f'✅ Добро пожаловать, {user.username}!', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('✅ Вы вышли из системы', 'info')
    return redirect(url_for('index'))


# ============================================================
#  ЛИЧНЫЙ КАБИНЕТ
# ============================================================
@app.route('/profile')
@login_required
def profile():
    # Проверяем не истёк ли премиум
    if current_user.is_premium and current_user.premium_until:
        if current_user.premium_until < datetime.now():
            current_user.is_premium = False
            current_user.searches_left = 0
            db.session.commit()
            flash('⚠️ Ваш тариф истёк. Оформите новый!', 'warning')

    searches = (SearchHistory.query
                .filter_by(user_id=current_user.id)
                .order_by(SearchHistory.searched_at.desc())
                .limit(20).all())

    searches_left = get_searches_left(current_user)

    return render_template('profile.html',
                           user=current_user,
                           searches=searches,
                           searches_left=searches_left,
                           prices=PRICES,
                           plan_names=PLAN_NAMES)


# ============================================================
#  ОПЛАТА
# ============================================================
@app.route('/payment')
@login_required
def payment():
    plan = request.args.get('plan', '1')
    if plan not in PRICES:
        flash('❌ Неверный тариф', 'danger')
        return redirect(url_for('pricing'))

    instruction = create_manual_payment_instruction(
        plan=plan,
        price=PRICES[plan],
        plan_name=PLAN_NAMES[plan],
        user_id=current_user.id,
        username=current_user.username
    )

    return render_template('payment.html',
                           plan=plan,
                           plan_name=PLAN_NAMES[plan],
                           price=PRICES[plan],
                           instruction=instruction)


@app.route('/payment/confirm', methods=['POST'])
@login_required
def payment_confirm():
    payment_id = request.form.get('payment_id', '').strip()
    plan       = request.form.get('plan', '').strip()

    if not payment_id or not plan:
        flash('❌ Ошибка отправки заявки', 'danger')
        return redirect(url_for('pricing'))

    notify_payment(
        payment_id=payment_id,
        username=current_user.username,
        plan_name=PLAN_NAMES.get(plan, plan),
        price=PRICES.get(plan, 0)
    )

    flash('✅ Заявка принята!', 'success')
    return redirect(url_for('profile'))

# ============================================================
#  ADMIN-ПАНЕЛЬ (упрощённая, защищена секретным ключом)
# ============================================================
@app.route('/admin')
def admin():
    key = request.args.get('key', '')
    if key != app.config['SECRET_KEY']:
        return "Нет доступа", 403

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', 
                           users=users, 
                           plan_names=PLAN_NAMES,
                           admin_key=key)  # ← добавили это


@app.route('/admin/activate', methods=['POST'])
def admin_activate():
    key = request.form.get('key', '')
    if key != app.config['SECRET_KEY']:
        return jsonify({"error": "Нет доступа"}), 403

    user_id = request.form.get('user_id', type=int)
    plan    = request.form.get('plan', '')

    if not user_id or plan not in PRICES:
        return jsonify({"error": "Неверные данные"}), 400

    success = activate_plan_manual(user_id, plan)
    if success:
        user = User.query.get(user_id)
        return jsonify({
            "ok": True,
            "message": f"✅ Тариф '{PLAN_NAMES[plan]}' активирован для {user.username}"
        })
    return jsonify({"error": "Пользователь не найден"}), 404


# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚗  AUTO KOREA — КЫРГЫЗСТАН")
    print("=" * 60)
    print("📌  http://127.0.0.1:5000")
    print()
    print("💰  Тарифы:")
    for plan_id, price in PRICES.items():
        print(f"    {PLAN_NAMES[plan_id]}: {price} сом")
    print()
    print("⚠️   Для остановки: Ctrl+C")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)