# Настройка TimeTracker бота на Render

Эта инструкция поможет вам настроить Telegram бота на платформе Render для непрерывной работы.

## Шаг 1: Подготовка репозитория

1. Убедитесь, что ваш репозиторий содержит следующие файлы:

   - `requirements.txt` - со всеми зависимостями
   - `Dockerfile` - для сборки Docker-контейнера (уже создан)

2. Добавьте файл `render.yaml` в корень проекта для настройки Render:

```yaml
services:
  - type: web
    name: timetracker-bot
    env: docker
    repo: https://github.com/steshenkoof/amibot.git
    branch: master
    buildCommand: docker build -t timetracker-bot .
    startCommand: python run_bot.py
    envVars:
      - key: POSTGRES_HOST
        sync: false
      - key: POSTGRES_PORT
        value: 5432
      - key: POSTGRES_USER
        sync: false
      - key: POSTGRES_PASSWORD
        sync: false
      - key: POSTGRES_DATABASE
        sync: false
    autoDeploy: true
```

## Шаг 2: Регистрация на Render

1. Перейдите на сайт [render.com](https://render.com/) и зарегистрируйтесь.
2. Возможно, потребуется использовать VPN для регистрации и настройки.

## Шаг 3: Создание базы данных PostgreSQL

1. В панели управления Render нажмите "New" и выберите "PostgreSQL".
2. Заполните необходимые поля:
   - Name: timetracker-db
   - Database: timetracker
   - User: postgres
   - Region: выберите ближайший к вам регион
   - PostgreSQL Version: 14
3. Нажмите "Create Database".
4. После создания базы данных сохраните данные подключения (хост, пароль).

## Шаг 4: Создание Web Service для бота

1. В панели управления Render нажмите "New" и выберите "Web Service".
2. Подключите свой GitHub репозиторий (потребуется авторизация в GitHub).
3. Выберите репозиторий с ботом.
4. Заполните настройки:
   - Name: timetracker-bot
   - Environment: Docker
   - Branch: master (или ваша основная ветка)
   - Build Command: оставьте пустым (используется Dockerfile)
   - Start Command: python run_bot.py
5. В разделе "Environment Variables" добавьте переменные окружения:
   - `POSTGRES_HOST`: [Internal Database URL из настроек вашей БД]
   - `POSTGRES_PORT`: 5432
   - `POSTGRES_USER`: postgres
   - `POSTGRES_PASSWORD`: [пароль из настроек БД]
   - `POSTGRES_DATABASE`: timetracker
6. Нажмите "Create Web Service".

## Шаг 5: Проверка работы

1. После успешного деплоя, перейдите в раздел "Logs" вашего сервиса для проверки работы бота.
2. Бот должен запуститься и подключиться к Telegram API.

## Важные замечания

1. **Бесплатный план Render** имеет ограничения:

   - Сервис "засыпает" после 15 минут неактивности
   - 750 часов бесплатного использования в месяц
   - Для непрерывной работы рекомендуется перейти на платный план ($7/месяц)

2. **Для предотвращения "засыпания"** можно настроить периодические HTTP-запросы к вашему сервису с помощью сервисов типа UptimeRobot или создать дополнительный эндпоинт в вашем боте.

3. **Обновление бота**: при пуше изменений в ваш GitHub репозиторий, Render автоматически пересоберет и перезапустит ваш сервис.

## Дополнительно: Настройка постоянной активности

Чтобы бот не "засыпал" на бесплатном плане, добавьте в ваш проект простой веб-сервер:

1. Добавьте в `requirements.txt` библиотеку Flask:

```
flask==2.0.1
```

2. Создайте файл `web_server.py` с кодом:

```python
from flask import Flask
import threading
import os
from bot import main

app = Flask(__name__)

@app.route('/')
def home():
    return "TimeTracker Bot is running!"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=main)
    bot_thread.start()

    # Запуск веб-сервера
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

3. Измените команду запуска в Render на:

```
python web_server.py
```

4. Зарегистрируйтесь на [UptimeRobot](https://uptimerobot.com/) и настройте мониторинг URL вашего сервиса (например, https://your-app.onrender.com/ping) с интервалом в 5 минут.
