import asyncio
from database import db

async def test_categories():
    """Test category functions"""
    print("🧪 Тестирование функций категорий...")
    
    try:
        # Initialize database
        await db.init_db()
        
        # Test getting users by category
        print("\n📊 Тест получения пользователей по категориям:")
        
        categories = ['кухня', 'зал', 'мойка']
        for category in categories:
            users = await db.get_users_by_category(category)
            print(f"  {category.title()}: {len(users)} пользователей")
            
        # Test getting all users
        all_users = await db.get_users_by_category()
        print(f"  Всего активных: {len(all_users)} пользователей")
        
        # Test getting archived users
        archived_users = await db.get_users_by_category(include_archived=True)
        archived_count = len([u for u in archived_users if u.get('is_archived', False)])
        print(f"  Архивированных: {archived_count} пользователей")
        
        print("\n✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_categories()) 