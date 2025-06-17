#!/usr/bin/env python3
"""
Скрипт для проверки и исправления статуса пользователя
"""
import asyncio
from database import db

async def check_and_fix_user():
    """Проверить и исправить статус пользователя"""
    # Ваш Telegram ID
    user_id = 5168428653
    username = "mansklav"
    display_name = "Mansklav"
    
    print(f"🔍 Проверяю пользователя ID: {user_id}")
    
    try:
        # Проверяем текущий статус
        status = await db.get_user_status(user_id)
        print(f"📊 Текущий статус: {status}")
        
        if status == 'new':
            print("❌ Пользователь не зарегистрирован")
            print("📝 Регистрирую пользователя...")
            
            # Регистрируем пользователя
            await db.register_user(user_id, username, display_name, display_name)
            
            # Одобряем автоматически (вы же админ)
            await db.approve_user(user_id, user_id)
            
            new_status = await db.get_user_status(user_id)
            print(f"✅ Новый статус: {new_status}")
            
        elif status == 'pending':
            print("⏳ Пользователь ждет одобрения")
            print("✅ Одобряю пользователя...")
            
            await db.approve_user(user_id, user_id)
            new_status = await db.get_user_status(user_id)
            print(f"✅ Новый статус: {new_status}")
            
        elif status == 'approved':
            print("✅ Пользователь уже одобрен")
            
        elif status == 'blocked':
            print("🚫 Пользователь заблокирован")
            # Можно разблокировать если нужно
            
        # Проверяем админские права
        from config import ADMIN_IDS
        print(f"👑 Список админов: {ADMIN_IDS}")
        
        if user_id in ADMIN_IDS:
            print("✅ У вас есть админские права")
        else:
            print("❌ У вас НЕТ админских прав!")
            print("🔧 Добавьте ваш ID в ADMIN_IDS в config.py")
        
        # Проверяем информацию о пользователе
        print("\n📋 Информация о пользователе:")
        user_info = await db.get_user_info(user_id) if hasattr(db, 'get_user_info') else None
        if user_info:
            print(f"  • ID: {user_info.get('user_id')}")
            print(f"  • Имя: {user_info.get('display_name')}")
            print(f"  • Username: {user_info.get('username')}")
            print(f"  • Статус: {user_info.get('status')}")
        else:
            print("  ❌ Не удалось получить информацию о пользователе")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_and_fix_user()) 