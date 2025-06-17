import psycopg2
from config import DATABASE_URL

def update_schema():
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔄 Обновление схемы базы данных...")
        
        # Проверяем существующие колонки
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users';
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📊 Существующие колонки: {existing_columns}")
        
        # Добавляем category если её нет
        if 'category' not in existing_columns:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN category VARCHAR(20) DEFAULT 'зал';
            """)
            conn.commit()
            print("✅ Добавлена колонка category")
        else:
            print("ℹ️ Колонка category уже существует")
        
        # Добавляем is_archived если её нет
        if 'is_archived' not in existing_columns:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
            print("✅ Добавлена колонка is_archived")
        else:
            print("ℹ️ Колонка is_archived уже существует")
        
        print("✅ Схема базы данных успешно обновлена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    update_schema() 