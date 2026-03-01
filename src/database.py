#src/database.py
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'encar_cars.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER UNIQUE,
            vin TEXT,
            manufacturer TEXT,
            manufacturer_ko TEXT,
            model TEXT,
            model_ko TEXT,
            year INTEGER,
            price INTEGER,
            mileage INTEGER,
            fuel_type TEXT,
            transmission TEXT,
            color TEXT,
            engine_capacity TEXT,
            images TEXT,
            description TEXT,
            original_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parse_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vehicles_found INTEGER,
            vehicles_added INTEGER,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных cars создана")

def save_car(car_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cars WHERE vehicle_id = ?", (car_data.get('vehicle_id'),))
    existing = cursor.fetchone()
    images_json = json.dumps(car_data.get('images', []), ensure_ascii=False)
    if existing:
        cursor.execute('''
            UPDATE cars SET
                vin = ?, manufacturer = ?, manufacturer_ko = ?, model = ?, model_ko = ?,
                year = ?, price = ?, mileage = ?, fuel_type = ?, transmission = ?, color = ?,
                engine_capacity = ?, images = ?, description = ?, original_url = ?
            WHERE vehicle_id = ?
        ''', (
            car_data.get('vin'), car_data.get('manufacturer'), car_data.get('manufacturer_ko'),
            car_data.get('model'), car_data.get('model_ko'), car_data.get('year'),
            car_data.get('price'), car_data.get('mileage'), car_data.get('fuel_type'),
            car_data.get('transmission'), car_data.get('color'), car_data.get('engine_capacity'),
            images_json, car_data.get('description'), car_data.get('original_url'),
            car_data.get('vehicle_id')
        ))
        added = False
    else:
        cursor.execute('''
            INSERT INTO cars (
                vehicle_id, vin, manufacturer, manufacturer_ko, model, model_ko,
                year, price, mileage, fuel_type, transmission, color,
                engine_capacity, images, description, original_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            car_data.get('vehicle_id'), car_data.get('vin'), car_data.get('manufacturer'),
            car_data.get('manufacturer_ko'), car_data.get('model'), car_data.get('model_ko'),
            car_data.get('year'), car_data.get('price'), car_data.get('mileage'),
            car_data.get('fuel_type'), car_data.get('transmission'), car_data.get('color'),
            car_data.get('engine_capacity'), images_json, car_data.get('description'),
            car_data.get('original_url')
        ))
        added = True
    conn.commit()
    conn.close()
    return added

def search_by_vin(vin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cars WHERE vin LIKE ? ORDER BY created_at DESC", (f'%{vin}%',))
    results = cursor.fetchall()
    conn.close()
    return results

def get_recent_cars(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cars ORDER BY created_at DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def log_parse_result(found, added, status="success"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO parse_history (vehicles_found, vehicles_added, status)
        VALUES (?, ?, ?)
    ''', (found, added, status))
    conn.commit()
    conn.close()