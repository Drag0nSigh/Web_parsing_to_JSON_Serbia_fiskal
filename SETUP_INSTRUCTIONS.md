# 🚀 Инструкция по запуску

## 1. Создайте файл .env

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

## 2. Запуск PostgreSQL

```bash
# Запуск контейнера PostgreSQL
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs postgres
```

## 3. Запуск бота

```bash
# Активация виртуального окружения
venv\Scripts\activate

# Установка зависимостей (если не установлены)
pip install -r requirements.txt

# Запуск бота
python src\bot_tg\start_bot.py
```

## 4. Проверка работы

1. Отправьте боту команду `/start`
2. Отправьте ссылку на сербский фискальный чек
3. Бот вернет JSON файл в российском формате

## 5. Админские команды

Если вы администратор (ADMIN_ID в .env), доступны команды:
- `/admin_start` - список админских команд
- `/admin_logs` - последние логи
- `/admin_users` - список пользователей
- `/admin_stats` - статистика использования
- `/admin_status` - статус системы
- `/admin_test` - тест работоспособности

## 6. Остановка

```bash
# Остановка бота
Ctrl+C

# Остановка PostgreSQL
docker compose down
```
