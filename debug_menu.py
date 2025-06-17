#!/usr/bin/env python3
"""
Скрипт для отладки проблемы с меню
"""
import asyncio
import logging
import sys
import os

# Настройка кодировки для Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Настройка детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_menu.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_menu():
    """Тестирование меню и обработчиков"""
    try:
        logger.info("=== НАЧАЛО ОТЛАДКИ МЕНЮ ===")
        
        # Проверяем конфигурацию
        from config import BOT_TOKEN, ADMIN_IDS
        logger.info(f"Bot token length: {len(BOT_TOKEN)}")
        logger.info(f"Admin IDs: {ADMIN_IDS}")
        
        # Проверяем импорты
        logger.info("Проверяем импорты...")
        from handlers.start import get_main_keyboard
        from handlers.work import router as work_router
        from handlers.reports import router as reports_router
        from handlers.admin import router as admin_router
        
        logger.info("✅ Все импорты успешны")
        
        # Тестируем клавиатуру
        logger.info("Тестируем создание клавиатуры...")
        keyboard = get_main_keyboard(5168428653)  # Ваш ID
        logger.info(f"Клавиатура создана: {len(keyboard.keyboard)} строк")
        
        for i, row in enumerate(keyboard.keyboard):
            logger.info(f"Строка {i}: {[btn.text for btn in row]}")
        
        # Проверяем обработчики
        logger.info("Проверяем регистрацию обработчиков...")
        logger.info(f"Work router handlers: {len(work_router.handlers)}")
        logger.info(f"Reports router handlers: {len(reports_router.handlers)}")
        logger.info(f"Admin router handlers: {len(admin_router.handlers)}")
        
        # Запускаем бота
        logger.info("Запускаем бота с отладкой...")
        from bot import main as bot_main
        await bot_main()
        
    except Exception as e:
        logger.error(f"ОШИБКА: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_menu()) 