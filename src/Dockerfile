# Используем легкую версию Python на базе Alpine Linux
FROM python:3.11-alpine

# Устанавливаем системные зависимости для Selenium и PostgreSQL
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    postgresql-dev \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Устанавливаем переменные окружения для Chrome
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/bin/chromium-browser
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Создаем симлинк для chromedriver
RUN ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver

# Создаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY src/ .

# Создаем пользователя для безопасности
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser


# Команда по умолчанию - запуск бота
CMD ["python", "bot_tg/start_bot.py"]
