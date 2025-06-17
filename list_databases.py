#!/usr/bin/env python3
import asyncio
import asyncpg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_databases():
    """List all PostgreSQL databases"""
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
        
        # Get PostgreSQL version
        version = await conn.fetchval('SELECT version()')
        logger.info(f"PostgreSQL version: {version}")
        
        # List all databases
        databases = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
        )
        
        logger.info("📋 Available databases:")
        for db in databases:
            logger.info(f"  - {db['datname']}")
        
        # Check for amichaisebase specifically
        amichaise_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'amichaisebase'"
        )
        
        if amichaise_exists:
            logger.info("✅ Database 'amichaisebase' found!")
        else:
            logger.info("❌ Database 'amichaisebase' not found!")
            
            # Try to find similar names
            similar = await conn.fetch(
                "SELECT datname FROM pg_database WHERE datname ILIKE '%amichaise%' OR datname ILIKE '%base%'"
            )
            if similar:
                logger.info("🔍 Similar database names found:")
                for db in similar:
                    logger.info(f"  - {db['datname']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(list_databases())
    if result:
        print("\n🎉 Database listing completed!")
    else:
        print("\n❌ Database listing failed!") 