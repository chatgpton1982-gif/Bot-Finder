FROM python:3.11-slim

# Зависимости для Telethon и Pyrogram
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN useradd -r -s /bin/false tg_bot

WORKDIR /opt/tg_bot_finder

# Копирование зависимостей и установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY bot/ bot/
COPY data/ data/

# Создание директории для данных
RUN mkdir -p data && chown -R tg_bot:tg_bot data

# Переключение на пользователя tg_bot
USER tg_bot

# Переменные окружения можно передать через docker run -e или docker-compose
# Критичные секреты (API_ID, API_HASH, PHONE_NUMBER) через -e или .env файл
# Обычные настройки (BOT_TOKEN, AI-ключи) через -e или .env файл

CMD ["python", "-m", "bot.main"]