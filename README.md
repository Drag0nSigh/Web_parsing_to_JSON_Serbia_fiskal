# 🤖 Парсер Сербских Фискальных Данных + Телеграм Бот

Проект для парсинга сербских фискальных данных из HTML и конвертации их в российский JSON формат с интеграцией в телеграм бота и полной системой логирования.

## 🚀 Возможности

✅ **Парсинг сербских фискальных чеков** - извлечение данных с сайта  
✅ **Конвертация в российский формат** - преобразование в JSON по образцу  
✅ **Телеграм бот** - автоматическая обработка ссылок  
✅ **Валидация данных** - проверка с помощью Pydantic  
✅ **Ежедневное логирование** - система логов с автоудалением старых файлов  
✅ **PostgreSQL база данных** - хранение логов и пользователей с Docker  
✅ **Администрирование** - команды для управления ботом и пользователями  
✅ **Docker поддержка** - два варианта: легковесный (Alpine) и полный (Slim)  
✅ **Система лимитов** - ограничения на количество запросов в день  
✅ **Отладочные файлы** - сохранение HTML для анализа проблем  

## 📁 Структура проекта

```
├── src/
│   ├── models/
│   │   └── fiscal_models.py    # Pydantic модели для валидации
│   ├── parser/
│   │   └── fiscal_parser.py    # Парсер с Selenium
│   ├── utils/
│   │   ├── timing_decorator.py # Декораторы для измерения времени
│   │   └── log_manager.py      # Менеджер ежедневных логов
│   ├── bot_tg/
│   │   ├── telegram_bot.py     # Основной телеграм бот
│   │   ├── admin_commands.py   # Админские команды
│   │   ├── user_commands.py    # Пользовательские команды
│   │   └── start_bot.py        # Скрипт запуска бота
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Менеджер базы данных
│   │   ├── models.py           # SQLAlchemy модели
│   │   ├── utils.py            # Утилиты для работы с БД
│   │   └── Dockerfile          # Dockerfile для PostgreSQL
│   ├── log/                    # Ежедневные логи (создается автоматически)
│   ├── main.py                 # Основной скрипт для тестирования
│   ├── Dockerfile              # Основной Dockerfile (Python Slim)
│   └── Dockerfile_lite         # Легковесный Dockerfile (Alpine)
├── .env                        # Настройки бота и БД
├── env_example.txt             # Пример настроек
├── docker-compose.yml          # Docker Compose конфигурация
├── requirements.txt            # Зависимости
└── README.md                   # Документация
```

## 🛠️ Установка

### 🐳 Docker (Рекомендуется)

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd Web_parsing_to_JSON_Serbia_fiskal
```

2. **Настройте .env файл**
```bash
cp env_example.txt .env
# Отредактируйте .env файл, добавьте ваши настройки
```

3. **Запустите проект**
```bash
# Сборка и запуск
docker compose up -d

# Просмотр логов
docker compose logs bot -f
```

### 🐍 Локальная установка

1. **Создание виртуального окружения**
```bash
python -m venv venv
```

2. **Активация окружения**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

## ⚙️ Настройка

### 1. Переменные окружения (.env)

Скопируйте `env_example.txt` в `.env` и настройте:

```env
# Настройки базы данных PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fiscal_data
POSTGRES_USER=fiscal_user
POSTGRES_PASSWORD=secure_password_123

# Настройки Telegram бота
TG_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_telegram_id_here

# Настройки логирования
LOG_RETENTION_DAYS=30

# Настройки лимитов
DAILY_REQUEST_LIMIT=50
```

### 2. Создание Telegram бота

1. Найдите **@BotFather** в Telegram
2. Отправьте `/newbot`
3. Введите имя и username бота
4. **Скопируйте токен** в `.env`

### 3. Получение ADMIN_ID

1. Напишите **@userinfobot** в Telegram
2. Скопируйте ваш ID в `ADMIN_ID` в `.env`

## 🚀 Запуск

### Docker

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов бота
docker compose logs bot -f

# Остановка
docker compose down
```

### Локально

```bash
# Запуск бота
cd src
python bot_tg/start_bot.py

# Тестовый парсинг
python main.py
```

## 💬 Использование бота

### Пользовательские команды:
- `/start` - приветствие и инструкции
- **Отправка ссылки** - автоматический парсинг и возврат JSON файла

### Административные команды:
- `/admin` - панель администратора
- `/activate <user_id>` - активация пользователя
- `/deactivate <user_id>` - деактивация пользователя
- **Кнопки админ-панели:**
  - 📝 Логи - просмотр системных логов
  - 👥 Пользователи - управление пользователями
  - 🧪 Тест - тестирование парсера
  - 📊 Статус - статус системы
  - 📈 Статистика - статистика использования

### Пример ссылки:
```
https://suf.purs.gov.rs/v/?vl=AzdWVDYyRUM0N1ZUNjJFQzQYWwEASVUBAHDBGAEAAAAAAAABmOyyJXMAAAAdrdjynx8FFJ7vKJSEWHehCSexnfVJwleCdnX8WapD...
```

## 📊 Формат результата

Бот возвращает JSON файл в формате **списка** :

```json
[
  {
    "_id": "уникальный_id_24_символа",
    "createdAt": "2025-08-27T20:02:34+00:00",
    "daily_requests": "3/50",
    "remaining_requests": 47,
    "ticket": {
      "document": {
        "receipt": {
          "cashTotalSum": 0,
          "code": 3,
          "creditSum": 0,
          "dateTime": "2025-08-27T20:02:34",
          "ecashTotalSum": 183996,
          "fiscalDocumentFormatVer": 4,
          "fiscalDocumentNumber": 88856,
          "fiscalDriveNumber": "0000000000000000",
          "fiscalSign": 87369,
          "fnsUrl": "www.nalog.gov.rs",
          "items": [
            {
              "name": "Dečiji jog.DUO-NEO/KOM/0216130",
              "quantity": 1,
              "price": 7998,
              "sum": 7998,
              "nds": 2,
              "paymentType": 4,
              "productType": 1
            }
          ],
          "kktRegId": "106884584",
          "nds0": 0,
          "amountsReceiptNds": {
            "amountsNds": [
              {
                "nds": 2,
                "ndsSum": 17597
              }
            ]
          },
          "operationType": 1,
          "retailPlace": "1228831-Prodavnica br. 0156",
          "retailPlaceAddress": "БУЛЕВАР ДЕСПОТА СТЕФАНА 99, БЕОГРАД (ПАЛИЛУЛА)",
          "taxationType": 2,
          "appliedTaxationType": 2,
          "totalSum": 183996,
          "user": "1228831-Prodavnica br. 0156",
          "userInn": "106884584"
        }
      }
    }
  }
]
```

## 📋 Система логирования

### Ежедневные логи (src/log/)
- `bot_YYYY-MM-DD.log` - основные логи бота
- `database_YYYY-MM-DD.log` - логи базы данных
- `parser_YYYY-MM-DD.log` - логи парсера
- `startup_YYYY-MM-DD.log` - логи запуска
- `debug_YYYY-MM-DD.html` - отладочные HTML файлы

### Автоудаление
- Старые логи удаляются автоматически через `LOG_RETENTION_DAYS` дней
- По умолчанию: 30 дней

### Docker логи
```bash
# Логи бота
docker compose logs bot -f

# Логи базы данных
docker compose logs postgres -f

# Логи внутри контейнера
docker compose exec bot ls -la /app/log
```



## 🔧 Технические детали

### Технологии:
- **Python 3.11+**
- **Selenium** для парсинга динамического контента
- **Pydantic** для валидации данных
- **python-telegram-bot** для бота
- **BeautifulSoup** для обработки HTML
- **PostgreSQL** для хранения данных
- **SQLAlchemy** для ORM
- **Docker** для контейнеризации

### Система базы данных:
- **Users** - пользователи бота
- **RequestLog** - логи запросов
- **Лимиты** - настраиваемое количество запросов в день (`DAILY_REQUEST_LIMIT`)
- **Активация** - админ может активировать/деактивировать пользователей

### Парсер:
- **Новый драйвер** для каждого запроса
- **Автоматическое закрытие** драйверов
- **Обработка Knockout.js** элементов
- **Robust число парсинг** для сербского формата

## ⚡ Производительность

### Время выполнения:
- **Запуск драйвера**: ~2-3s
- **Парсинг данных**: ~1-2s  
- **Общее время**: ~4-5s на запрос

### Мониторинг:
- Встроенная система мониторинга в админ-панели
- Статистика использования системных ресурсов
- Отслеживание количества запросов

## 🔒 Безопасность

- ✅ Валидация всех входящих данных
- ✅ Обработка ошибок и исключений
- ✅ Автоматическое закрытие драйверов
- ✅ Изоляция каждого запроса
- ✅ Система лимитов запросов
- ✅ Административный контроль доступа
- ✅ Graceful fallback при ошибках логирования

## 🆘 Troubleshooting

### Частые проблемы:

1. **ChromeDriver ошибки**
   ```bash
   # Docker
   docker compose exec bot chromedriver --version
   
   # Локально
   pip install --upgrade selenium webdriver-manager
   ```

2. **База данных недоступна**
   ```bash
   # Проверка статуса
   docker compose ps
   
   # Перезапуск БД
   docker compose restart postgres
   ```

3. **Логи не создаются**
   ```bash
   # Проверка прав доступа
   docker compose exec bot ls -la /app/log
   
   # Локально
   ls -la src/log
   ```

4. **Ошибки парсинга**
   - Проверьте отладочные HTML файлы в `log/debug_*.html`
   - Убедитесь в доступности сайта
   - Проверьте формат ссылки

### Логи для отладки:
```bash
# Подробные логи бота
docker compose logs bot --tail=100

# Логи базы данных
docker compose logs postgres --tail=50

# Логи внутри контейнера
docker compose exec bot tail -f /app/log/bot_$(date +%Y-%m-%d).log
```

## 🔄 Архитектура

### Компоненты:
- **Telegram Bot** - обработка команд и сообщений
- **Parser** - извлечение данных с сербского сайта
- **Database** - PostgreSQL для хранения данных
- **Log Manager** - система ежедневного логирования
- **Admin Panel** - веб-интерфейс управления через бота

### Паттерны:
- **Context Managers** - автоматическое управление ресурсами
- **Dependency Injection** - изолированные компоненты
- **Command Pattern** - структурированные команды бота
- **Observer Pattern** - система логирования

## 📈 Мониторинг

### Метрики доступные через админ-панель:
- 💻 Использование CPU и RAM
- 📊 Статистика запросов по пользователям
- 📝 Количество и размер лог-файлов
- 👥 Активные/неактивные пользователи
- 🕐 Время последней активности

### Команды для мониторинга:
```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats

# Размер логов
docker compose exec bot du -sh /app/log/*
```