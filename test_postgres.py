#!/usr/bin/env python3
import asyncio
import asyncpg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        # Connection parameters
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='0665191213',
            database='amichaisebase'
        )
        
        logger.info("✅ Successfully connected to PostgreSQL database!")
        
        # Test query
        result = await conn.fetchval('SELECT version()')
        logger.info(f"PostgreSQL version: {result}")
        
        # Test creating table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("✅ Test table created successfully!")
        
        # Test insert
        await conn.execute(
            'INSERT INTO test_table (name) VALUES ($1)', 
            'test_connection'
        )
        logger.info("✅ Test data inserted successfully!")
        
        # Test select
        rows = await conn.fetch('SELECT * FROM test_table LIMIT 5')
        logger.info(f"✅ Found {len(rows)} rows in test table")
        
        # Clean up test table
        await conn.execute('DROP TABLE IF EXISTS test_table')
        logger.info("✅ Test table cleaned up!")
        
        await conn.close()
        logger.info("✅ Database connection test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_postgres_connection())
    if result:
        print("\n🎉 PostgreSQL connection test PASSED!")
    else:
        print("\n❌ PostgreSQL connection test FAILED!") 