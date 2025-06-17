#!/usr/bin/env python3
import asyncio
import asyncpg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_database():
    """Create amichaisebase database"""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='0665191213',
            database='postgres'  # Connect to default database
        )
        
        logger.info("✅ Connected to PostgreSQL server!")
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'amichaisebase'"
        )
        
        if db_exists:
            logger.info("Database 'amichaisebase' already exists!")
        else:
            # Create database
            await conn.execute('CREATE DATABASE amichaisebase')
            logger.info("✅ Database 'amichaisebase' created successfully!")
        
        await conn.close()
        
        # Now test connection to our new database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='0665191213',
            database='amichaisebase'
        )
        
        logger.info("✅ Successfully connected to amichaisebase database!")
        
        # Get database info
        result = await conn.fetchval('SELECT current_database()')
        logger.info(f"Current database: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database creation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(create_database())
    if result:
        print("\n🎉 Database creation completed successfully!")
    else:
        print("\n❌ Database creation failed!") 