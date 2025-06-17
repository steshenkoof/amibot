import asyncio
import asyncpg
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from config import POSTGRES_CONFIG

logger = logging.getLogger(__name__)

class PostgresDatabase:
    def __init__(self):
        self.pool = None
    
    async def init_db(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=POSTGRES_CONFIG['host'],
                port=POSTGRES_CONFIG['port'],
                user=POSTGRES_CONFIG['user'],
                password=POSTGRES_CONFIG['password'],
                database=POSTGRES_CONFIG['database'],
                min_size=1,
                max_size=10
            )
            
            logger.info("✅ Connected to PostgreSQL database successfully!")
            
            # Create tables
            await self._create_tables()
            logger.info("✅ Database tables created/verified successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    async def _create_tables(self):
        """Create all necessary tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    display_name TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'pending',
                    category TEXT DEFAULT 'зал',
                    is_archived BOOLEAN DEFAULT FALSE,
                    archived_at TIMESTAMP,
                    approved_by BIGINT,
                    approved_at TIMESTAMP,
                    first_seen TIMESTAMP,
                    last_active TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add phone column if it doesn't exist (for existing databases)
            try:
                await conn.execute('ALTER TABLE users ADD COLUMN phone TEXT')
            except asyncpg.exceptions.DuplicateColumnError:
                pass  # Column already exists
            
            # Ensure work_sessions table has all necessary columns before creating it
            try:
                # This ensures the column exists for older databases before the table is potentially created
                await conn.execute('ALTER TABLE work_sessions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except asyncpg.exceptions.UndefinedTableError:
                # The table doesn't exist yet, it will be created with the column below.
                pass
            except asyncpg.exceptions.DuplicateColumnError:
                # The column already exists, which is fine.
                pass

            # Work sessions table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    date DATE NOT NULL,
                    check_in_time TIMESTAMP,
                    check_out_time TIMESTAMP,
                    total_duration INTEGER,  -- minutes
                    location_checkin_lat REAL,
                    location_checkin_lon REAL,
                    location_checkout_lat REAL,
                    location_checkout_lon REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON work_sessions(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_date ON work_sessions(date)')
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def get_user_status(self, user_id: int) -> str:
        """Get user status"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                'SELECT status FROM users WHERE user_id = $1', user_id
            )
            return result if result else 'new'
    
    async def add_or_update_user(self, user_id: int, username: str = None, full_name: str = None, display_name: str = None):
        """Add or update user information"""
        async with self.pool.acquire() as conn:
            # Check if user exists
            existing = await conn.fetchval('SELECT status FROM users WHERE user_id = $1', user_id)
            
            if existing:
                # Update existing user
                await conn.execute('''
                    UPDATE users 
                    SET username = $1, full_name = $2, display_name = COALESCE($3, display_name), last_active = $4
                    WHERE user_id = $5
                ''', username, full_name, display_name, datetime.now(), user_id)
            else:
                # Create new user with pending status
                await conn.execute('''
                    INSERT INTO users (user_id, username, full_name, display_name, status, last_active)
                    VALUES ($1, $2, $3, $4, 'pending', $5)
                ''', user_id, username, full_name, display_name, datetime.now())
    
    async def register_user(self, user_id: int, username: str, full_name: str, display_name: str):
        """Register new user with pending status"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, full_name, display_name, status, first_seen, last_active)
                VALUES ($1, $2, $3, $4, 'pending', $5, $6)
                ON CONFLICT (user_id) DO UPDATE SET
                username = $2, full_name = $3, display_name = $4, last_active = $6
            ''', user_id, username, full_name, display_name, datetime.now(), datetime.now())
    
    async def register_user_extended(self, user_id: int, username: str, full_name: str, 
                                   display_name: str, phone: str, category: str):
        """Register new user with extended information"""
        valid_categories = ['кухня', 'зал', 'мойка', 'бар']
        if category not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, full_name, display_name, phone, category, status, first_seen, last_active)
                VALUES ($1, $2, $3, $4, $5, $6, 'pending', $7, $8)
                ON CONFLICT (user_id) DO UPDATE SET
                username = $2, full_name = $3, display_name = $4, phone = $5, category = $6, status = 'pending', last_active = $8
            ''', user_id, username, full_name, display_name, phone, category, datetime.now(), datetime.now())
    
    async def approve_user(self, user_id: int, admin_id: int):
        """Approve user"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET status = 'approved', approved_by = $1, approved_at = $2
                WHERE user_id = $3
            ''', admin_id, datetime.now(), user_id)
    
    async def block_user(self, user_id: int):
        """Block user"""
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET status = $1 WHERE user_id = $2', 'blocked', user_id)
    
    async def archive_user(self, user_id: int, admin_id: int):
        """Archive user (soft delete - keeps all data)"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET is_archived = TRUE, archived_at = $1, status = 'archived'
                WHERE user_id = $2
            ''', datetime.now(), user_id)
    
    async def set_user_category(self, user_id: int, category: str):
        """Set user category (кухня, зал, мойка, бар)"""
        valid_categories = ['кухня', 'зал', 'мойка', 'бар']
        if category not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET category = $1 WHERE user_id = $2', category, user_id)
    
    async def get_users_by_category(self, category: str = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get users filtered by category"""
        async with self.pool.acquire() as conn:
            query = '''
                SELECT user_id, username, full_name, display_name, status, category, is_archived, last_active
                FROM users 
                WHERE 1=1
            '''
            params = []
            
            if not include_archived:
                query += ' AND is_archived = FALSE'
            
            if category:
                query += f' AND category = ${len(params) + 1}'
                params.append(category)
            
            query += ' ORDER BY category, display_name, full_name'
            
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            
            return [dict(row) for row in rows]
    
    async def get_pending_users(self) -> List[Dict[str, Any]]:
        """Get users waiting for approval"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, username, full_name, display_name, phone, category, first_seen
                FROM users 
                WHERE status = 'pending'
                ORDER BY first_seen DESC
            ''')
            
            return [dict(row) for row in rows]
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by user_id"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT user_id, username, full_name, display_name, status, category, 
                       is_archived, archived_at, approved_by, approved_at, 
                       first_seen, last_active
                FROM users 
                WHERE user_id = $1
            ''', user_id)
            
            return dict(row) if row else None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users with their status"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, username, full_name, display_name, status, first_seen, last_active
                FROM users 
                ORDER BY display_name, full_name
            ''')
            
            return [dict(row) for row in rows]
    
    async def check_in(self, user_id: int, username: str, full_name: str, 
                      latitude: float, longitude: float) -> bool:
        """Check in user for work"""
        today = date.today()
        
        async with self.pool.acquire() as conn:
            # Check if user already checked in today
            existing = await conn.fetchval('''
                SELECT id FROM work_sessions 
                WHERE user_id = $1 AND date = $2 AND check_in_time IS NOT NULL
            ''', user_id, today)
            
            if existing:
                return False  # Already checked in
            
            # Create new work session
            await conn.execute('''
                INSERT INTO work_sessions 
                (user_id, username, full_name, date, check_in_time, location_checkin_lat, location_checkin_lon)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', user_id, username, full_name, today, datetime.now(), latitude, longitude)
            
            return True
    
    async def check_in_with_time(self, user_id: int, checkin_datetime: datetime) -> (bool, str):
        """Check in user for work with custom time"""
        today = checkin_datetime.date()
        
        async with self.pool.acquire() as conn:
            # Check if user already checked in today
            existing = await conn.fetchval('''
                SELECT id FROM work_sessions 
                WHERE user_id = $1 AND date = $2 AND check_in_time IS NOT NULL
            ''', user_id, today)
            
            if existing:
                return False, "Сотрудник уже отметил приход сегодня."

            user_info = await self.get_user_info(user_id)
            if not user_info:
                return False, "Пользователь не найден."
            
            # Create new work session with custom time
            await conn.execute('''
                INSERT INTO work_sessions 
                (user_id, username, full_name, date, check_in_time, location_checkin_lat, location_checkin_lon)
                VALUES ($1, $2, $3, $4, $5, NULL, NULL)
            ''', user_id, user_info.get('username'), user_info.get('full_name'), today, checkin_datetime)
            
            return True, "Приход успешно зарегистрирован."
    
    async def check_out(self, user_id: int, latitude: float = None, longitude: float = None) -> Optional[int]:
        """Check out user from work, returns total minutes worked"""
        today = date.today()
        
        async with self.pool.acquire() as conn:
            # Find today's work session
            session = await conn.fetchrow('''
                SELECT id, check_in_time FROM work_sessions 
                WHERE user_id = $1 AND date = $2 AND check_in_time IS NOT NULL AND check_out_time IS NULL
            ''', user_id, today)
            
            if not session:
                return None  # No active session
            
            session_id, check_in_time = session['id'], session['check_in_time']
            check_out_time = datetime.now()
            
            # Calculate duration in minutes
            duration = int((check_out_time - check_in_time).total_seconds() / 60)
            
            # Update session
            await conn.execute('''
                UPDATE work_sessions 
                SET check_out_time = $1, total_duration = $2, location_checkout_lat = $3, location_checkout_lon = $4
                WHERE id = $5
            ''', check_out_time, duration, latitude, longitude, session_id)
            
            return duration
    
    async def check_out_with_time(self, user_id: int, checkout_datetime: datetime) -> (Optional[int], str):
        """Check out user from work with custom time, returns total minutes worked"""
        today = checkout_datetime.date()
        
        async with self.pool.acquire() as conn:
            # Find today's work session
            session = await conn.fetchrow('''
                SELECT id, check_in_time FROM work_sessions 
                WHERE user_id = $1 AND date = $2 AND check_in_time IS NOT NULL AND check_out_time IS NULL
            ''', user_id, today)
            
            if not session:
                return None, "У сотрудника нет активной смены для завершения."
            
            session_id, check_in_time = session['id'], session['check_in_time']
            
            if checkout_datetime < check_in_time:
                return None, "Время ухода не может быть раньше времени прихода."

            # Calculate duration in minutes
            duration = int((checkout_datetime - check_in_time).total_seconds() / 60)
            
            # Update session with custom time
            await conn.execute('''
                UPDATE work_sessions 
                SET check_out_time = $1, total_duration = $2, location_checkout_lat = $3, location_checkout_lon = $4
                WHERE id = $5
            ''', checkout_datetime, duration, None, None, session_id)
            
            return duration, f"Уход успешно зарегистрирован. Отработано: {duration} минут."
    
    async def get_user_stats(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get user statistics for specified number of days"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT date, check_in_time, check_out_time, total_duration
                FROM work_sessions 
                WHERE user_id = $1 AND date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC
            ''' % days, user_id)
            
            result = []
            for row in rows:
                result.append({
                    'date': row['date'].isoformat(),
                    'check_in': row['check_in_time'].isoformat() if row['check_in_time'] else None,
                    'check_out': row['check_out_time'].isoformat() if row['check_out_time'] else None,
                    'duration_minutes': row['total_duration'] or 0
                })
            
            return result
    
    async def get_today_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get today's work session for user"""
        today = date.today()
        
        async with self.pool.acquire() as conn:
            session = await conn.fetchrow('''
                SELECT check_in_time, check_out_time, total_duration
                FROM work_sessions 
                WHERE user_id = $1 AND date = $2
            ''', user_id, today)
            
            if session:
                return {
                    'check_in': session['check_in_time'].isoformat() if session['check_in_time'] else None,
                    'check_out': session['check_out_time'].isoformat() if session['check_out_time'] else None,
                    'duration_minutes': session['total_duration'] or 0
                }
            return None
    
    async def get_all_users_stats(self, start_date, end_date, category: str = None) -> List[Dict[str, Any]]:
        """Get statistics for all users in date range (for admin)"""
        # Ensure dates are proper date objects
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
            
        async with self.pool.acquire() as conn:
            query = '''
                SELECT ws.user_id, ws.username, ws.full_name, ws.date, 
                       ws.check_in_time, ws.check_out_time, ws.total_duration,
                       u.category, u.is_archived, u.phone
                FROM work_sessions ws
                LEFT JOIN users u ON ws.user_id = u.user_id
                WHERE ws.date BETWEEN $1 AND $2
            '''
            params = [start_date, end_date]
            
            if category:
                query += f' AND u.category = ${len(params) + 1}'
                params.append(category)
            
            query += ' ORDER BY u.category, ws.date DESC, ws.user_id'
            
            rows = await conn.fetch(query, *params)
            
            result = []
            for row in rows:
                result.append({
                    'user_id': row['user_id'],
                    'username': row['username'] or 'Unknown',
                    'full_name': row['full_name'] or 'Unknown',
                    'phone': row['phone'] or 'Не указан',
                    'category': row['category'] or 'зал',
                    'archived': row['is_archived'] or False,
                    'date': row['date'].isoformat(),
                    'check_in': row['check_in_time'].isoformat() if row['check_in_time'] else None,
                    'check_out': row['check_out_time'].isoformat() if row['check_out_time'] else None,
                    'duration_minutes': row['total_duration'] or 0
                })
            
            return result
    
    async def get_users_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get users filtered by status (e.g., 'approved', 'pending')."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, username, full_name, display_name, status, category, is_archived, last_active
                FROM users 
                WHERE status = $1 AND is_archived = FALSE
                ORDER BY display_name, full_name
            ''', status)
            return [dict(row) for row in rows]

# Create database instance
db = PostgresDatabase() 