#!/usr/bin/env python3
"""
Главный скрипт запуска всей системы:
- Telegram бот
- Web server для точной геолокации
- PostgreSQL база данных
"""
import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_bot():
    """Запуск Telegram бота"""
    try:
        from bot import main as bot_main
        logger.info("🤖 Запускаем Telegram бота...")
        await bot_main()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

async def run_web_server():
    """Запуск веб-сервера"""
    try:
        from web_server import start_web_server
        logger.info("🌐 Запускаем веб-сервер...")
        await start_web_server()
    except Exception as e:
        logger.error(f"Ошибка запуска веб-сервера: {e}")

async def main():
    """Главная функция запуска всей системы"""
    logger.info("🚀 Запуск TimeTracker системы...")
    
    # Создаем задачи для параллельного выполнения
    tasks = [
        asyncio.create_task(run_bot(), name="telegram_bot"),
        asyncio.create_task(run_web_server(), name="web_server")
    ]
    
    try:
        # Запускаем все задачи параллельно
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
        # Отменяем все задачи
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Все сервисы остановлены")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запускаем главную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Система остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 