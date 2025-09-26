# 🗄️ Настройка базы данных PostgreSQL

Инструкция по настройке PostgreSQL с помощью Docker для проекта парсинга фискальных данных.

## 📋 Требования

- Docker
- Docker Compose

## ⚙️ Настройка

### 1. Создайте файл .env

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Telegram Bot Configuration
TG_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_id_here

# PostgreSQL Database Configuration
POSTGRES_DB=fiscal_data
POSTGRES_USER=fiscal_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Database URL for SQLAlchemy
DATABASE_URL=postgresql://fiscal_user:secure_password_123@localhost:5432/fiscal_data
```

### 2. Запуск базы данных

```bash
# Запуск PostgreSQL контейнера
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs postgres
```

### 3. Инициализация базы данных

База данных инициализируется автоматически при первом запуске бота через SQLAlchemy:

```bash
# Запуск бота (автоматически создаст таблицы)
python src/bot_tg/start_bot.py
```

### 4. Остановка базы данных

```bash
# Остановка контейнера
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

## 🗂️ Структура базы данных

База данных автоматически инициализируется при первом запуске через SQLAlchemy ORM.

### Таблицы

#### `fiscal.users`
- `id` - первичный ключ
- `telegram_id` - ID пользователя в Telegram (уникальный)
- `username` - имя пользователя в Telegram
- `is_active` - статус активности пользователя
- `created_at` - дата создания записи
- `last_activity` - дата последней активности

#### `fiscal.request_logs`
- `id` - первичный ключ
- `user_id` - ID пользователя (внешний ключ)
- `username` - имя пользователя на момент запроса
- `status` - статус запроса (success/error)
- `error_message` - сообщение об ошибке (если есть)
- `created_at` - дата создания записи

## 🔧 Подключение к базе данных

### Через psql

```bash
# Подключение к контейнеру
docker exec -it fiscal_postgres psql -U fiscal_user -d fiscal_data

# Или через порт
psql -h localhost -p 5432 -U fiscal_user -d fiscal_data
```

### Через Python

```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)
```

## 📊 Мониторинг

### Проверка здоровья контейнера

```bash
docker-compose ps
```

### Просмотр логов

```bash
docker-compose logs -f postgres
```

### Статистика использования

```bash
docker stats fiscal_postgres
```

## 🛠️ Полезные команды

```bash
# Перезапуск контейнера
docker-compose restart postgres

# Обновление контейнера
docker-compose pull
docker-compose up -d

# Резервное копирование
docker exec fiscal_postgres pg_dump -U fiscal_user fiscal_data > backup.sql

# Восстановление из резервной копии
docker exec -i fiscal_postgres psql -U fiscal_user fiscal_data < backup.sql
```

## 🔒 Безопасность

- Измените пароли по умолчанию
- Используйте сильные пароли
- Ограничьте доступ к порту 5432
- Регулярно создавайте резервные копии

## 📝 Примечания

- Данные сохраняются в Docker volume `postgres_data`
- Скрипты инициализации находятся в `db/init-scripts/`
- Контейнер автоматически перезапускается при сбоях
