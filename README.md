# 🤖 Парсер Сербских Фискальных Данных + Телеграм Бот

Проект для парсинга сербских фискальных данных из HTML и конвертации их в российский JSON формат с интеграцией в телеграм бота.

## 🚀 Возможности

✅ **Парсинг сербских фискальных чеков** - извлечение данных с сайта  
✅ **Конвертация в российский формат** - преобразование в JSON по образцу  
✅ **Телеграм бот** - автоматическая обработка ссылок  
✅ **Валидация данных** - проверка с помощью Pydantic  
✅ **Сохранение логов** - каждый результат сохраняется с временной меткой  
✅ **Измерение производительности** - декораторы для отслеживания времени выполнения  
✅ **PostgreSQL база данных** - хранение логов и пользователей с Docker  
✅ **Администрирование** - команды для управления ботом

## 📁 Структура проекта

```
├── src/
│   ├── models/
│   │   └── fiscal_models.py    # Pydantic модели для валидации
│   ├── parser/
│   │   └── fiscal_parser.py    # Парсер с Selenium
│   ├── utils/
│   │   └── timing_decorator.py # Декораторы для измерения времени
│   ├── bot_tg/
│   │   ├── telegram_bot.py     # Основной телеграм бот
│   │   ├── admin_commands.py   # Админские команды
│   │   └── start_bot.py        # Скрипт запуска бота
│   └── main.py                 # Основной скрипт для тестирования
├── db/
│   └── Dockerfile              # Dockerfile для PostgreSQL
├── .env                        # Настройки бота и БД
├── docker-compose.yml          # Docker Compose конфигурация
├── log/                        # Папка с логами запросов
├── requirements.txt            # Зависимости
├── DATABASE_SETUP.md           # Инструкция по настройке БД
├── ADMIN_README.md             # Документация админских команд
└── README.md                   # Документация
```

## 🛠️ Установка

### 1. Создание виртуального окружения
```bash
python -m venv venv
```

### 2. Активация окружения
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 🗄️ Настройка базы данных

### 1. Установка Docker
Убедитесь, что у вас установлен Docker и Docker Compose.

### 2. Настройка .env
Добавьте в файл `.env` настройки базы данных:
```.env
# PostgreSQL Database Configuration
POSTGRES_DB=fiscal_data
POSTGRES_USER=fiscal_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://fiscal_user:secure_password_123@localhost:5432/fiscal_data
```

### 3. Запуск PostgreSQL
```bash
# Запуск базы данных
docker compose up -d

# Проверка статуса
docker compose ps
```

Подробная инструкция в [DATABASE_SETUP.md](DATABASE_SETUP.md)

## 🤖 Настройка телеграм бота

### 1. Создание бота
1. Найдите **@BotFather** в Telegram
2. Отправьте `/newbot`
3. Введите имя и username бота
4. **Скопируйте токен**

### 2. Настройка .env
Откройте файл `.env` и добавьте:
```.env
TG_TOKEN=ваш_токен_от_BotFather
```

## 🚀 Запуск

### Телеграм бот
```bash
# Через скрипт запуска (рекомендуется)
venv\Scripts\python.exe src\bot_tg\start_bot.py

# Прямой запуск бота
venv\Scripts\python.exe src\bot_tg\telegram_bot.py
```

### Основной скрипт (для тестирования)
```bash
venv\Scripts\python.exe src\main.py
```

## 💬 Использование бота

### Команды:
- `/start` - приветствие и инструкции
- Отправка ссылки - парсинг и возврат JSON файла

### Пример ссылки:
```
https://suf.purs.gov.rs/v/?vl=AzdWVDYyRUM0N1ZUNjJFQzQYWwEASVUBAHDBGAEAAAAAAAABmOyyJXMAAAAdrdjynx8FFJ7vKJSEWHehCSexnfVJwleCdnX8WapD%2FVqiutLId1kOu75ZXt4Z%2Bsp4oPEXjlYGf0jXnO6%2FcXPw%2FPXq9hZr9uVlrxjhiEVvc44J3xYEaqN2AGIwBxT%2Bco7LOqgAfE6PBUeQlA49tC%2FCvCkGuiVwfXwQfXAHyhDIs3Q29%2FfrLFsGoTpXECXvyKW%2FAg%2BxTXUFlO1zSxraDy2PbDNA%2FYSEYknv0LxtxUxuMU6FUL0fOXGM%2BmXcfYzRkDkjomzsdpiFGzuN9nRThzv16Q4S%2B9aznut5Fb2LWB85BaH4y11GtXMwubfQNzsdUpJZObMDZXcRx4V8tefqUmGlai%2FgEeT6FSrjHMGEP62UgDtokyrzuCqNeMz6JkZuHxE%2FqkLxZnYGwGUx5nRpiGEME1UyLQNUcWFsQgkJiyvWL3FpZsuRjXahZiNM5glVo1bbeISMK8%2BO8BsTPSHAg0jZkGpvi9OOT4qY8T0Zf1OMG4BnVTNM28h5ZMqobV8pjydfj%2BJtvsaDuNdv5C4Nhj3IC%2BaLeQdLFoL%2FfkA2%2F50HWUCi8KWMLVQHwYbJftNfYjPhjlrmbgG3FuDTWPM%2Bakut5GIUu4D8d1wmpqgQBenYX2qnqmcWhfNQu%2FBHz1KhizKvh2NLz%2FjWWiPicWVVM8H2cdU%2BGy4qdKkdk0WKiEtK362QBJnPpz%2BiUEFBoR6osNg%3D
```

## 📊 Формат результата

Бот возвращает JSON файл в формате:
```json
[
  {
    "_id": "уникальный_id",
    "createdAt": "2025-08-27T20:02:34+00:00",
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
          "items": [...],
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
          "operator": null,
          "prepaidSum": 0,
          "provisionSum": 0,
          "requestNumber": null,
          "retailPlace": "1228831-Prodavnica br. 0156",
          "retailPlaceAddress": "БУЛЕВАР ДЕСПОТА СТЕФАНА 99, БЕОГРАД (ПАЛИЛУЛА)",
          "shiftNumber": null,
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

## 🔧 Технические детали

- **Python 3.8+**
- **Selenium** для парсинга динамического контента
- **Pydantic** для валидации данных
- **python-telegram-bot** для бота
- **BeautifulSoup** для обработки HTML
- **webdriver-manager** для автоматического управления Chrome WebDriver

## 📝 Модели данных

### SerbianFiscalData
- `tin` - ИНН организации
- `shop_name` - название магазина
- `shop_address` - адрес магазина
- `city` - город
- `sdc_date_time` - дата и время операции
- `total_amount` - общая сумма
- `total_counter` - счетчик документов
- `transaction_type_counter` - счетчик типа транзакции
- `items` - список товаров

### FiscalData
- `_id` - уникальный идентификатор
- `createdAt` - дата создания
- `ticket` - билет с фискальными данными

## ⚡ Производительность

### Время выполнения:
- **Запуск драйвера**: ~2.5s
- **Парсинг данных**: ~1.5s
- **Общее время**: ~4s на запрос

### Логирование:
- **Ежедневные логи** - файлы `requests_log_YYYY-MM-DD.txt`
- **Измерение времени** - декораторы показывают время выполнения функций
- **Отладочная информация** - подробные логи процесса парсинга

## 🔒 Безопасность

- Валидация всех входящих данных
- Обработка ошибок и исключений
- Автоматическое закрытие драйверов
- Изоляция каждого запроса

## 📚 Документация

- `BOT_README.md` - подробная документация бота
- `requirements.txt` - список зависимостей
- `src/utils/timing_decorator.py` - декораторы для измерения времени

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи в консоли
2. Убедитесь в правильности токена
3. Проверьте доступность интернета
4. Убедитесь, что Chrome установлен
5. Проверьте файлы логов в папке `log/`

## 🔄 Архитектура

### Простая архитектура:
- **Новый драйвер при каждом запросе** - изоляция и надежность
- **Автоматическое закрытие** - благодаря `with` statement
- **Синхронная обработка** - простота и стабильность
- **Измерение производительности** - встроенные декораторы времени