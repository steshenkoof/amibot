#!/usr/bin/env python3
"""
Скрипт для обновления схемы базы данных
Добавляет новые поля для категорий и архивирования
"""
import asyncio
import logging
from database import db
import psycopg2
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_database_schema():
    """Update database schema with new columns"""
    await db.init_db()
    
    async with db.pool.acquire() as conn:
        try:
            # Add new columns if they don't exist
            logger.info("Adding new columns to users table...")
            
            # Check if columns exist and add them if they don't
            columns_to_add = [
                ("category", "TEXT DEFAULT 'зал'"),
                ("archived", "BOOLEAN DEFAULT FALSE"),
                ("archived_at", "TIMESTAMP"),
                ("approved_by", "BIGINT"),
                ("approved_at", "TIMESTAMP"), 
                ("first_seen", "TIMESTAMP"),
                ("last_active", "TIMESTAMP")
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    await conn.execute(f'''
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                    ''')
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            # Update existing users to have default values
            logger.info("Updating existing users with default values...")
            
            await conn.execute('''
                UPDATE users 
                SET category = COALESCE(category, 'зал'),
                    archived = COALESCE(archived, FALSE),
                    first_seen = COALESCE(first_seen, created_at),
                    last_active = COALESCE(last_active, created_at)
                WHERE category IS NULL OR archived IS NULL OR first_seen IS NULL OR last_active IS NULL
            ''')
            
            logger.info("✅ Database schema updated successfully!")
            
            # Show current users with categories
            users = await conn.fetch('SELECT user_id, full_name, category, archived FROM users')
            logger.info(f"\nCurrent users ({len(users)}):")
            for user in users:
                status = "🗃 ARCHIVED" if user['archived'] else "✅ ACTIVE"
                logger.info(f"• {user['full_name']} - {user['category']} - {status}")
                
        except Exception as e:
            logger.error(f"❌ Error updating database schema: {e}")
            raise
        finally:
            await db.close()

def update_database_schema():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔄 Обновление схемы базы данных...")
        
        # Добавляем колонку category если её нет
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN category VARCHAR(20) DEFAULT 'зал';
            """)
            print("✅ Добавлена колонка category")
        except psycopg2.errors.DuplicateColumn:
            print("ℹ️ Колонка category уже существует")
        
        # Добавляем колонку is_archived если её нет
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
            """)
            print("✅ Добавлена колонка is_archived")
        except psycopg2.errors.DuplicateColumn:
            print("ℹ️ Колонка is_archived уже существует")
        
        # Создаем индекс для быстрого поиска активных пользователей
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_active 
                ON users (is_archived) WHERE is_archived = FALSE;
            """)
            print("✅ Создан индекс для активных пользователей")
        except Exception as e:
            print(f"ℹ️ Индекс уже существует: {e}")
        
        # Создаем индекс для категорий
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_category 
                ON users (category);
            """)
            print("✅ Создан индекс для категорий")
        except Exception as e:
            print(f"ℹ️ Индекс уже существует: {e}")
        
        conn.commit()
        print("✅ Схема базы данных успешно обновлена!")
        
        # Проверяем текущую структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📊 Текущая структура таблицы users:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (default: {col[2]})")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении схемы: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database_schema() 