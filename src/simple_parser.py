#Src/simple_parser.py
import random
from datetime import datetime

class EncarParser:
    def __init__(self):
        self.stats = {'total_found': 0, 'total_added': 0, 'errors': 0}

    def parse_latest_vehicles(self, limit=20):
        print(f"🚗 Генерируем {limit} тестовых автомобилей...")
        korean_cars = [
            {"manufacturer": "Hyundai", "manufacturer_ko": "현대",
             "models": [("Sonata", "쏘나타"), ("Santa Fe", "싼타페"), ("Tucson", "투싼")]},
            {"manufacturer": "Kia", "manufacturer_ko": "기아",
             "models": [("Sorento", "쏘렌토"), ("Sportage", "스포티지"), ("K5", "K5")]},
            {"manufacturer": "Genesis", "manufacturer_ko": "제네시스",
             "models": [("G80", "G80"), ("G70", "G70"), ("GV80", "GV80")]},
        ]
        fuel_types = ['Бензин', 'Дизель', 'Гибрид']
        transmissions = ['Автомат', 'Механика']
        colors = ['Белый', 'Черный', 'Серебристый', 'Синий', 'Красный']

        vehicles = []
        for i in range(limit):
            brand = random.choice(korean_cars)
            model_pair = random.choice(brand["models"])
            year = random.randint(2018, 2024)
            vin = f"KMH{random.randint(10000,99999)}{random.randint(1000,9999)}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"
            vehicle = {
                'vehicle_id': 1000000 + i,
                'vin': vin,
                'manufacturer': brand["manufacturer"],
                'manufacturer_ko': brand["manufacturer_ko"],
                'model': model_pair[0],
                'model_ko': model_pair[1],
                'year': year,
                'price': random.randint(15000000, 50000000),
                'mileage': random.randint(0, 80000),
                'fuel_type': random.choice(fuel_types),
                'transmission': random.choice(transmissions),
                'color': random.choice(colors),
                'engine_capacity': f"{random.choice(['2.0', '2.5', '3.3'])}L",
                'images': ['https://via.placeholder.com/800x600?text=Car+Photo'] * 3,
                'description': f'{brand["manufacturer"]} {model_pair[0]} {year} из Кореи',
                'original_url': f'https://encar.com/detail?carId={1000000 + i}'
            }
            vehicles.append(vehicle)
            self.stats['total_added'] += 1
            print(f"  ✅ Добавлен: {vehicle['manufacturer']} {vehicle['model']} ({vehicle['year']})")
        self.stats['total_found'] = len(vehicles)
        return vehicles

    def get_stats(self):
        return self.stats