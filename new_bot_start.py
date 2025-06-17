#!/usr/bin/env python3
"""
Скрипт для проверки и запуска бота с новым токеном
"""
import asyncio
import requests
import time
import logging
import sys
import os

# Настройка кодировки для Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Настройка логирования без эмодзи
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('new_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from config import BOT_TOKEN

def test_new_token():
    """Тестирование нового токена"""
    try:
        logger.info("Тестирование нового токена...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            logger.info(f"УСПЕХ! Новый бот подключен:")
            logger.info(f"  - Имя: {bot_info.get('first_name')}")
            logger.info(f"  - Username: @{bot_info.get('username')}")
            logger.info(f"  - ID: {bot_info.get('id')}")
            return True
        else:
            logger.error(f"ОШИБКА подключения: {result}")
            return False
    except Exception as e:
        logger.error(f"ОШИБКА тестирования токена: {e}")
        return False

def clear_webhook():
    """Очистка webhook для нового бота"""
    try:
        logger.info("Очистка webhook...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("Webhook очищен успешно")
        else:
            logger.warning(f"Проблема с очисткой webhook: {result}")
    except Exception as e:
        logger.error(f"Ошибка очистки webhook: {e}")

async def start_new_bot():
    """Запуск нового бота"""
    try:
        logger.info("Запуск нового бота...")
        
        # Импортируем и запускаем бота
        from bot import main as bot_main
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("ЗАПУСК НОВОГО БОТА")
    logger.info("=" * 50)
    
    # 1. Тестируем новый токен
    if not test_new_token():
        logger.error("Не удалось подключиться с новым токеном!")
        return False
    
    # 2. Очищаем webhook
    clear_webhook()
    
    # 3. Пауза для стабилизации
    logger.info("Пауза 5 секунд для стабилизации...")
    time.sleep(5)
    
    # 4. Запускаем бота
    logger.info("Запускаем бота с новым токеном...")
    await start_new_bot()
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Запуск прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1) 