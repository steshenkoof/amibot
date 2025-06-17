FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка зависимостей для gspread
RUN pip install --no-cache-dir gspread oauth2client

# Копирование кода
COPY . .

# Запуск бота
CMD ["python", "run_bot.py"] 