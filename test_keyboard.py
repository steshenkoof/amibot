#!/usr/bin/env python3
"""
Тестовый скрипт для проверки клавиатуры бота
"""
import requests
from config import BOT_TOKEN

def send_test_message():
    """Отправить тестовое сообщение себе"""
    # Замените на ваш Telegram ID
    chat_id = "5168428653"  # Ваш chat_id
    
    message = "Тест клавиатуры! Напишите любое сообщение боту."
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if result.get('ok'):
        print("✅ Тестовое сообщение отправлено!")
        print(f"Message ID: {result['result']['message_id']}")
    else:
        print(f"❌ Ошибка: {result}")

if __name__ == "__main__":
    send_test_message() 