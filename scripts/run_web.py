# scripts/run_web.py
import sys
import os
from flask import Flask, render_template, request

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database import get_connection, search_by_vin, get_recent_cars
from src.utils import format_price, parse_images
import json

app = Flask(__name__,
            template_folder='../web/templates',
            static_folder='../web/static')

@app.route('/')
def index():
    """Главная страница"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем статистику
    cursor.execute("SELECT COUNT(*) FROM cars")
    total_cars = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(created_at) FROM cars")
    last_update = cursor.fetchone()[0] or "Нет данных"
    
    # Получаем последние 6 машин
    recent = get_recent_cars(6)
    
    conn.close()
    
    return render_template('index.html', 
                         stats={'total_cars': total_cars, 'last_update': last_update},
                         recent_cars=recent)

@app.route('/search')
def search():
    """Страница результатов поиска"""
    vin_query = request.args.get('vin', '')
    
    if not vin_query:
        return "Введите VIN для поиска", 400
    
    results = search_by_vin(vin_query)
    
    # Преобразуем результаты для шаблона
    cars = []
    for row in results:
        car = dict(row)
        # Парсим изображения
        if car.get('images'):
            car['images'] = parse_images(car['images'])
        cars.append(car)
    
    return render_template('search.html', 
                         cars=cars,
                         query=vin_query)

@app.route('/recent')
def recent():
    """Последние добавленные"""
    cars = get_recent_cars(20)
    
    # Преобразуем для шаблона
    cars_list = []
    for row in cars:
        car = dict(row)
        if car.get('images'):
            car['images'] = parse_images(car['images'])
        cars_list.append(car)
    
    return render_template('search.html', 
                         cars=cars_list,
                         query="последние добавленные")

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 Запуск веб-сервера")
    print("=" * 50)
    print("\n📁 Откройте браузер и перейдите по адресу:")
    print("👉 http://127.0.0.1:5000")
    print("\n⚠️ Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    app.run(debug=True)