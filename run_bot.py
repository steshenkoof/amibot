#!/usr/bin/env python3
"""
Простой скрипт запуска только Telegram бота
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Настройка логирования без эмодзи для Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск только бота"""
    try:
        logger.info("Запускаем TimeTracker бота...")
        
        # Импортируем и запускаем бота
        from bot import main as bot_main
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот завершен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1) 