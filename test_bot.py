import requests

TOKEN = '8612052994:AAGG-XaXcCmTFY_2KNDva8tJVHcxnNUA3Mo'
CHAT_ID = '838737337'

url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
r = requests.post(url, json={'chat_id': CHAT_ID, 'text': 'Тест!'})
print(r.status_code, r.json())