#!/usr/bin/env python3
"""
Простой скрипт запуска бота
"""
import asyncio
import logging
import sys
import os

# Настройка кодировки для Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Простое логирование без эмодзи
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска"""
    try:
        logger.info("Запуск TimeTracker бота...")
        
        # Проверяем токен
        from config import BOT_TOKEN
        if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("Не установлен токен бота!")
            return
        
        logger.info(f"Токен загружен: {len(BOT_TOKEN)} символов")
        
        # Запускаем бота
        from bot import main as bot_main
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 