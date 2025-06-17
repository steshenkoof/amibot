#!/usr/bin/env python3
"""
Скрипт для тестирования всех роутеров
"""
import asyncio
import logging
import sys
import os

# Настройка кодировки для Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_routers.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_routers():
    """Тестирование всех роутеров"""
    try:
        logger.info("=== ТЕСТИРОВАНИЕ РОУТЕРОВ ===")
        
        # Проверяем конфигурацию
        from config import BOT_TOKEN, ADMIN_IDS
        logger.info(f"Токен бота: {len(BOT_TOKEN)} символов")
        logger.info(f"Админы: {ADMIN_IDS}")
        
        # Проверяем импорты роутеров
        logger.info("Проверяем импорты роутеров...")
        
        from handlers.start import router as start_router
        from handlers.work import router as work_router
        from handlers.reports import router as reports_router
        from handlers.admin import router as admin_router
        from handlers.registration import router as registration_router
        
        logger.info("✅ Все роутеры импортированы успешно")
        
        # Проверяем клавиатуру
        logger.info("Проверяем клавиатуру...")
        from handlers.start import get_main_keyboard
        keyboard = get_main_keyboard(5168428653)  # Ваш ID как админа
        
        logger.info(f"Клавиатура создана: {len(keyboard.keyboard)} строк")
        for i, row in enumerate(keyboard.keyboard):
            logger.info(f"  Строка {i}: {[btn.text for btn in row]}")
        
        # Проверяем, что роутеры созданы корректно
        logger.info("Проверяем роутеры...")
        routers = {
            "start": start_router,
            "work": work_router,
            "reports": reports_router,
            "admin": admin_router,
            "registration": registration_router
        }
        
        for name, router in routers.items():
            logger.info(f"  ✅ {name} router: {type(router).__name__}")
        
        # Проверяем конкретные кнопки в импортах
        logger.info("Проверяем импорты для кнопок...")
        
        # Проверяем grep поиском основные кнопки
        import subprocess
        import os
        
        # Проверяем кнопку админ панели
        try:
            result = subprocess.run(
                ['grep', '-r', '👨‍💼 Админ панель', 'handlers/'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                logger.info("  ✅ Найден обработчик кнопки 'Админ панель'")
            else:
                logger.warning("  ⚠️  Не найден обработчик кнопки 'Админ панель'")
        except FileNotFoundError:
            # grep не найден (Windows), используем альтернативный способ
            logger.info("  📝 Поиск grep не доступен, проверяем файлы напрямую...")
            
            # Читаем файл admin.py
            with open('handlers/admin.py', 'r', encoding='utf-8') as f:
                admin_content = f.read()
                if '👨‍💼 Админ панель' in admin_content:
                    logger.info("  ✅ Найден обработчик кнопки 'Админ панель' в admin.py")
                else:
                    logger.warning("  ⚠️  Не найден обработчик кнопки 'Админ панель' в admin.py")
        
        # Проверяем порядок роутеров в bot.py
        logger.info("Проверяем порядок роутеров в bot.py...")
        with open('bot.py', 'r', encoding='utf-8') as f:
            bot_content = f.read()
            
        if 'dp.include_router(admin.router)' in bot_content:
            admin_pos = bot_content.find('dp.include_router(admin.router)')
            start_pos = bot_content.find('dp.include_router(start.router)')
            
            if admin_pos < start_pos:
                logger.info("  ✅ Порядок роутеров правильный: admin перед start")
            else:
                logger.warning("  ⚠️  Неправильный порядок роутеров: start перед admin")
        
        logger.info("=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        return True
        
    except Exception as e:
        logger.error(f"ОШИБКА: {e}", exc_info=True)
        return False

async def main():
    """Основная функция"""
    logger.info("Запуск тестирования роутеров...")
    
    # Сначала тестируем роутеры
    if not test_routers():
        logger.error("Тестирование роутеров провалено!")
        return
    
    logger.info("Тестирование роутеров успешно! Запускаем бота...")
    
    # Затем запускаем бота
    try:
        from bot import main as bot_main
        await bot_main()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 