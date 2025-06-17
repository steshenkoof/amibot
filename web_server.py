from flask import Flask
import threading
import asyncio
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("web_server")

app = Flask(__name__)

@app.route('/')
def home():
    return "TimeTracker Bot is running!"

@app.route('/ping')
def ping():
    return "pong"

def run_bot():
    """Запускает бота в отдельном потоке"""
    from bot import main
    
    logger.info("Запуск бота в отдельном потоке")
    
    # Создаем и запускаем новый event loop для асинхронных функций
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # Поток будет автоматически завершен при выходе из программы
    bot_thread.start()
    
    logger.info("Запуск веб-сервера Flask")
    
    # Запуск веб-сервера
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 