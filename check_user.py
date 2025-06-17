#!/usr/bin/env python3
"""
Скрипт для проверки статуса пользователя
"""
import asyncio
from database import db

async def check_user():
    """Проверить статус пользователя"""
    # Замените на ваш Telegram ID
    user_id = 5168428653  # Ваш ID
    
    print(f"Проверяю пользователя ID: {user_id}")
    
    try:
        status = await db.get_user_status(user_id)
        print(f"Статус пользователя: {status}")
        
        if status == 'new':
            print("❌ Пользователь не зарегистрирован")
        elif status == 'pending':
            print("⏳ Пользователь ожидает одобрения")
        elif status == 'approved':
            print("✅ Пользователь одобрен - должен видеть меню")
        elif status == 'blocked':
            print("🚫 Пользователь заблокирован")
        else:
            print(f"❓ Неизвестный статус: {status}")
        
        # Попробуем одобрить пользователя если он pending
        if status == 'pending':
            print("Попытка одобрить пользователя...")
            await db.approve_user(user_id)
            new_status = await db.get_user_status(user_id)
            print(f"Новый статус: {new_status}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(check_user()) 