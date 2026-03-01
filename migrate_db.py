# migrate_db.py
import sqlite3
import os

print("🔄 Обновление базы данных users.db...")

# Удаляем старую базу если есть проблемы
if os.path.exists('users.db'):
    print("🗑️ Удаляем старую базу данных...")
    os.remove('users.db')
    print("✅ Старая база удалена")
else:
    print("📁 База данных не найдена, создадим новую")

print("\n📊 База данных будет создана заново при следующем запуске app.py")
print("👉 Просто запустите: python app.py")