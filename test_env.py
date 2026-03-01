from dotenv import load_dotenv
import os
load_dotenv()

token = os.environ.get('TELEGRAM_TOKEN', 'НЕ НАЙДЕН')
chat_id = os.environ.get('TELEGRAM_CHAT_ID', 'НЕ НАЙДЕН')
print(f'TOKEN: {token[:20]}...')
print(f'CHAT_ID: {chat_id}')