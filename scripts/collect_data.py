import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.simple_parser import EncarParser
from src.database import init_database, save_car, log_parse_result

def main():
    print("=" * 60)
    print("🚗 ТЕСТОВЫЙ РЕЖИМ - ГЕНЕРАЦИЯ ДАННЫХ")
    print("=" * 60)

    init_database()
    parser = EncarParser()

    try:
        limit = input("\n📊 Сколько машин сгенерировать? (по умолчанию 5): ")
        limit = int(limit) if limit.strip() else 5
    except:
        limit = 5

    print(f"\n🚗 Генерируем {limit} тестовых автомобилей...")
    vehicles = parser.parse_latest_vehicles(limit=limit)

    print("\n💾 Сохраняем в базу данных...")
    added_count = 0
    for vehicle in vehicles:
        if save_car(vehicle):
            added_count += 1
            print(f"   ✅ Сохранён: {vehicle['manufacturer']} {vehicle['model']} ({vehicle['year']})")

    log_parse_result(len(vehicles), added_count)

    print("\n" + "=" * 60)
    print("📊 ИТОГИ:")
    print(f"   📦 Сгенерировано: {len(vehicles)} автомобилей")
    print(f"   💾 Сохранено в БД: {added_count}")
    print(f"   ❌ Ошибок: {parser.get_stats()['errors']}")
    print("=" * 60)
    print("\n✅ ГОТОВО! Теперь запустите сайт: python app.py")

if __name__ == "__main__":
    main()