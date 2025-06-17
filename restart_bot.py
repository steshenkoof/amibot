#!/usr/bin/env python3
"""
Скрипт для полной очистки и безопасного перезапуска бота
"""
import asyncio
import requests
import subprocess
import sys
import time
import logging
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def kill_python_processes():
    """Завершить все процессы Python"""
    try:
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Завершены процессы python.exe")
            
            result = subprocess.run(['taskkill', '/F', '/IM', 'python3.11.exe'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Завершены процессы python3.11.exe")
        else:
            # Linux/Mac
            subprocess.run(['pkill', '-f', 'python.*bot'], check=False)
            logger.info("✅ Завершены процессы python bot")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось завершить все процессы: {e}")

def clear_webhook():
    """Очистить webhook"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Webhook очищен")
        else:
            logger.warning(f"⚠️ Проблема с очисткой webhook: {result}")
            
        # Проверим статус
        info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        info_response = requests.get(info_url, timeout=10)
        info_result = info_response.json()
        
        if info_result.get('ok'):
            webhook_info = info_result.get('result', {})
            if not webhook_info.get('url'):
                logger.info("✅ Webhook отсутствует - готов к polling")
            else:
                logger.warning(f"⚠️ Webhook все еще установлен: {webhook_info.get('url')}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке webhook: {e}")

def wait_for_telegram():
    """Подождать, пока Telegram освободит соединения"""
    logger.info("⏳ Ожидание освобождения соединений Telegram...")
    time.sleep(10)  # Ждем 10 секунд
    logger.info("✅ Ожидание завершено")

async def test_bot_connection():
    """Тест подключения к боту"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            logger.info(f"✅ Бот подключен: @{bot_info.get('username')}")
            return True
        else:
            logger.error(f"❌ Ошибка подключения к боту: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ Не удалось подключиться к боту: {e}")
        return False

async def main():
    """Главная функция"""
    logger.info("🔄 Начинаем полную перезагрузку бота...")
    
    # 1. Завершить все процессы Python
    logger.info("1️⃣ Завершение всех процессов Python...")
    kill_python_processes()
    
    # 2. Очистить webhook
    logger.info("2️⃣ Очистка webhook...")
    clear_webhook()
    
    # 3. Подождать освобождения ресурсов
    logger.info("3️⃣ Ожидание освобождения ресурсов...")
    wait_for_telegram()
    
    # 4. Тест подключения
    logger.info("4️⃣ Тестирование подключения...")
    if not await test_bot_connection():
        logger.error("❌ Не удалось подключиться к боту!")
        return False
    
    # 5. Запуск бота
    logger.info("5️⃣ Запуск бота...")
    try:
        from bot import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            logger.info("✅ Бот успешно запущен!")
        else:
            logger.error("❌ Не удалось запустить бота!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("👋 Перезагрузка прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1) 