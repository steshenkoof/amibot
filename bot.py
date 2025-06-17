import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import db
from handlers import start, work, reports, admin, registration
from utils.schedule import schedule_manager

# Global bot instance for handlers
bot = None

# Configure logging with UTF-8 encoding
import sys
import io
import os

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """Set bot commands menu"""
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="work", description="🏢 Рабочее меню"),
        BotCommand(command="stats", description="📊 Моя статистика"),
        BotCommand(command="report", description="📈 Отчеты"),
        BotCommand(command="admin", description="⚙️ Админ панель"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Bot commands menu set successfully")

async def main():
    """Main function to start the bot"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set your bot token in config.py!")
        return
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        await db.init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return
        
    # Initialize schedule manager
    logger.info("Initializing schedule manager...")
    try:
        await schedule_manager.setup()
        logger.info("Schedule manager initialized successfully!")
    except Exception as e:
        logger.error(f"Schedule manager initialization failed: {e}")
        # Continue anyway, as this is not critical
    
    # Create bot and dispatcher
    global bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Include routers - specific handlers first, then general
    dp.include_router(admin.router)      # Admin handlers first
    dp.include_router(work.router)       # Work handlers
    dp.include_router(reports.router)    # Reports handlers  
    dp.include_router(registration.router) # Registration handlers
    dp.include_router(start.router)      # General handler last (has catch-all)
    
    # Add error handler
    @dp.error()
    async def error_handler(event):
        exception = event.exception
        update = event.update
        logger.error(f"Update {update} caused error {exception}")
        return True
    
    # Set bot commands menu
    await set_bot_commands(bot)
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()
        if hasattr(db, 'pool') and db.pool:
            await db.pool.close()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 