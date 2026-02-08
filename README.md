# 🤖 Парсер Сербских Фискальных Данных + Телеграм Бот

Проект для парсинга сербских фискальных данных из HTML и конвертации их в российский JSON формат для импорта в программу AlzexFinance с интеграцией в телеграм бота и полной системой логирования.

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
✅ **Комплексное тестирование** - 284 теста с покрытием 90%+
✅ **GitHub Actions CI/CD** - автоматизированные workflows для качества кода

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
├── tests/                      # Тестовая структура (284 теста)
│   ├── test_models.py          # Тесты Pydantic моделей
│   ├── test_database_manager.py # Тесты БД (37 тестов, 90%+ покрытие)
│   ├── test_db_utils.py        # Тесты утилит БД
│   ├── test_parser.py          # Тесты парсера
│   ├── test_bot_commands.py    # Тесты пользовательских команд
│   ├── test_admin_commands.py  # Тесты админских команд
│   ├── test_telegram_bot.py    # Тесты телеграм бота
│   ├── test_log_manager.py     # Тесты менеджера логов
│   ├── test_integration.py     # Интеграционные тесты
│   ├── conftest.py             # Фикстуры и настройки
│   ├── requirements-test.txt   # Зависимости для тестов
│   └── TESTING_GUIDE.md        # Руководство по тестированию
├── .github/                    # GitHub Actions
│   └── workflows/              # CI/CD автоматизация
│       ├── ci-cd.yml           # Проверка кода, тесты и деплой
│       └── README.md           # Документация CI/CD
├── .env                        # Настройки бота и БД
├── env_example.txt             # Пример настроек
├── docker-compose.yml          # Docker Compose конфигурация
├── requirements.txt            # Зависимости
├── pytest.ini                 # Конфигурация pytest
├── .coveragerc                 # Конфигурация покрытия кода
├── Makefile                    # Автоматизация команд
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

3. **Создайте необходимые папки (если запускаете локально)**
```bash
# Создание папки для логов
mkdir -p log

# Установка правильных прав доступа
chmod 755 log
```

4. **Запустите проект**
```bash
# Сборка и запуск
docker compose up -d

# Просмотр логов
docker compose logs bot -f
```

> **⚠️ Важно для продакшена**: При деплое на сервер убедитесь, что пользователь `fiskal_serbia_deploy` имеет права на папку `/opt/fiscal-parser` и все подпапки (см. раздел "Настройка сервера для деплоя" ниже).

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

4. **Настройка pre-commit (опционально)**
```bash
# Установка pre-commit hooks для автоматической проверки кода
pre-commit install
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
docker-compose up -d

# Просмотр логов бота
docker-compose logs bot -f

# Остановка
docker-compose down
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
- **pytest** для тестирования (284 теста, 90%+ покрытие)
- **GitHub Actions** для CI (автоматическая проверка кода)
- **Pre-commit hooks** для проверки кода перед коммитом

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
- ✅ Комплексное тестирование с покрытием 90%+
- ✅ Мокирование внешних зависимостей в тестах

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
docker-compose ps

# Перезапуск БД
docker-compose restart postgres
   ```

3. **Логи не создаются**
   ```bash
   # Проверка прав доступа
   docker-compose exec bot ls -la /app/log

   # Локально
   ls -la src/log
   ```

4. **Ошибки парсинга**
   - Проверьте отладочные HTML файлы в `log/debug_*.html`
   - Убедитесь в доступности сайта
   - Проверьте формат ссылки

5. **Ошибки деплоя CI/CD**
   ```bash
   # Проблема: "sudo: a terminal is required to read the password"
   # Решение: Пользователь fiskal_serbia_deploy НЕ должен быть в sudo
   sudo usermod -r fiskal_serbia_deploy sudo  # Удалить из sudo

   # Проблема: "rm: cannot remove '/opt/fiscal-parser': Permission denied"
   # Решение: Исправить права доступа на папку
   sudo chown -R fiskal_serbia_deploy:fiskal_serbia_deploy /opt/fiscal-parser
   sudo chmod -R 755 /opt/fiscal-parser

   # Проблема: "Can't find a suitable configuration file"
   # Решение: Проверить права на /opt/fiscal-parser
   ls -la /opt/fiscal-parser/

   # Проблема: Docker permission denied
   # Решение: Пользователь должен быть в группе docker
   sudo usermod -aG docker fiskal_serbia_deploy
   newgrp docker  # Применить группу

   # Проблема: "The POSTGRES_DB variable is not set"
   # Решение: .env файл должен быть создан один раз на сервере
   # См. раздел "4.1. Создание .env файла на сервере" выше

   # Проблема: "HTTPConnection.request() got an unexpected keyword argument 'chunked'"
   # Причина: Docker Compose 1.29.2 несовместим с новым Docker API (urllib3 конфликт)
   # Решение: Запуск через docker run напрямую с переменными из .env

   # Остановить старые контейнеры
   docker stop fiscal_bot fiscal_postgres 2>/dev/null || true
   docker rm fiscal_bot fiscal_postgres 2>/dev/null || true

   # Создать сеть и запустить сервисы
   docker network create fiscal_network 2>/dev/null || true
   docker run -d --name fiscal_postgres --network fiscal_network \
     --env-file .env -p 5432:5432 postgres:15
   sleep 10  # Ждем запуска БД

   # Проверить подключение к PostgreSQL
   docker exec fiscal_postgres pg_isready -U fiscal_user -d fiscal_data

   # Собрать и запустить бота
   docker build -t fiscal_bot -f src/Dockerfile .
   docker run -d --name fiscal_bot --network fiscal_network \
     --env-file .env \
     -e POSTGRES_HOST=postgres \
     -v ./log:/app/log fiscal_bot

   # Проверить подключение между контейнерами
   docker exec fiscal_bot ping -c 1 postgres

   # Если бот не может найти postgres (DNS проблема):

   # 1. Проверить статус PostgreSQL контейнера
   docker ps --filter "name=fiscal_postgres"
   docker logs fiscal_postgres

   # 2. Получить IP адрес PostgreSQL (разные способы)
   POSTGRES_IP=$(docker inspect fiscal_postgres --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
   echo "PostgreSQL IP (method 1): $POSTGRES_IP"

   # Альтернативный способ получения IP
   NETWORK_ID=$(docker inspect fiscal_postgres --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}')
   POSTGRES_IP=$(docker network inspect "$NETWORK_ID" --format='{{range .Containers}}{{if eq .Name "fiscal_postgres"}}{{.IPv4Address}}{{end}}{{end}}' | cut -d'/' -f1)
   echo "PostgreSQL IP (method 2): $POSTGRES_IP"

   # 3. Если IP пустой, попробовать подключение через localhost
   if [ -z "$POSTGRES_IP" ] || [ "$POSTGRES_IP" = "<no value>" ]; then
     echo "⚠️ Cannot get PostgreSQL IP, trying localhost connection..."
     docker stop fiscal_bot
     docker rm fiscal_bot
     docker run -d --name fiscal_bot \
       --env-file .env \
       -e POSTGRES_HOST=host.docker.internal \
       -v ./log:/app/log fiscal_bot
   else
     # 4. Перезапустить бота с IP адресом
     docker stop fiscal_bot
     docker rm fiscal_bot
     docker run -d --name fiscal_bot --network fiscal_network \
       --env-file .env \
       -e POSTGRES_HOST="$POSTGRES_IP" \
       -v ./log:/app/log fiscal_bot
   fi

   # Если PostgreSQL не запускается, попробовать простую команду:
   docker run --rm -d --name test_postgres \
     -e POSTGRES_DB=test -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test \
     -p 5433:5432 postgres:15

   # Проверить что контейнер запустился
   docker ps | grep test_postgres

   # Если ошибка "Role TG_BOT does not exist" - нужно пересоздать базу данных:
   # 1. Остановить контейнеры
   docker stop fiscal_bot fiscal_postgres 2>/dev/null || true
   docker rm fiscal_bot fiscal_postgres 2>/dev/null || true

   # 2. Удалить старый volume с базой данных
   docker volume rm fiscal_postgres_data 2>/dev/null || echo "Volume not found"

   # 3. Запустить PostgreSQL заново (он создаст базу с правильными пользователями)
   docker network create fiscal_network 2>/dev/null || true
   docker run -d --name fiscal_postgres --network fiscal_network \
     --env-file .env \
     -p 5432:5432 \
     -v fiscal_postgres_data:/var/lib/postgresql/data \
     postgres:15

   # 4. Подождать инициализации (30 секунд)
   sleep 30

   # 5. Проверить что пользователь создался
   docker exec fiscal_postgres psql -U postgres -c "\du"
   ```

### Логи для отладки:
```bash
# Подробные логи бота
docker-compose logs bot --tail=100

# Логи базы данных
docker-compose logs postgres --tail=50

# Логи внутри контейнера
docker-compose exec bot tail -f /app/log/bot_$(date +%Y-%m-%d).log
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
docker-compose ps

# Использование ресурсов
docker stats

# Размер логов
docker-compose exec bot du -sh /app/log/*
```

## 🚀 GitHub Actions CI/CD

### Автоматическая проверка кода и деплой

Полнофункциональный CI/CD workflow для поддержания качества и автоматического деплоя:

#### ✅ Что проверяется:
- **Форматирование**: Black (line-length=120) для единого стиля кода
- **Импорты**: isort для сортировки импортов
- **Линтинг**: Flake8 для качества кода (мягкие правила для совместимости)
- **Тестирование**: 284 теста с PostgreSQL и Selenium
- **Покрытие**: Минимум 80% покрытия кода
- **Chrome установка**: Автоматическая установка Google Chrome для тестов
- **База данных**: Инициализация PostgreSQL и проверка подключения
- **Деплой**: Автоматический деплой в production при push в main

#### 🔧 Автоматические настройки в CI:
- **Python 3.12** - последняя стабильная версия
- **PostgreSQL 15** - тестовая база данных
- **Chrome Browser** - для Selenium тестов
- **WebDriver Manager** - автоматическое управление драйверами
- **Кэширование зависимостей** - ускорение сборки

#### 🔧 Pre-commit hooks:
Настроены автоматические проверки перед коммитом:
```bash
# Установка pre-commit hooks
pre-commit install

# Запуск вручную на всех файлах
pre-commit run --all-files
```

#### 🔄 Когда запускается:
- При push в `main`, `develop`
- При создании/обновлении Pull Request

#### 📊 Badge статуса:
```markdown
![CI/CD](https://github.com/username/repo/workflows/CI-CD/badge.svg)
```

#### 🔧 Настройка сервера для деплоя:

##### 1. Создание пользователя для деплоя на сервере:

```bash
# Создание пользователя для деплоя
sudo useradd -m -s /bin/bash fiskal_serbia_deploy

# Добавление пользователя в группу docker
sudo usermod -aG docker fiskal_serbia_deploy

# НЕ добавляем в sudo - пользователь будет работать только с Docker
# sudo usermod -aG sudo fiskal_serbia_deploy

# ВАЖНО: Перезайти в систему для применения групп
# Или выполнить: newgrp docker
sudo su - fiskal_serbia_deploy

# Проверка групп пользователя
groups
```

##### 2. Создание необходимых папок:

```bash
# Создание директории проекта (как указано в CI)
sudo mkdir -p /opt/fiscal-parser

# КРИТИЧНО: Назначение прав пользователю деплоя
# Пользователь fiskal_serbia_deploy должен быть владельцем этой папки
sudo chown -R fiskal_serbia_deploy:fiskal_serbia_deploy /opt/fiscal-parser

# Установка правильных прав доступа
sudo chmod -R 755 /opt/fiscal-parser

# Создание папки для логов (для монтирования в Docker)
sudo mkdir -p /opt/fiscal-parser/log
sudo chown -R fiskal_serbia_deploy:fiskal_serbia_deploy /opt/fiscal-parser/log
sudo chmod -R 755 /opt/fiscal-parser/log

# Создание папки для данных PostgreSQL (если нужно)
sudo mkdir -p /var/lib/docker/volumes/fiscal_parser_postgres_data
sudo chown -R fiskal_serbia_deploy:fiskal_serbia_deploy /var/lib/docker/volumes/fiscal_parser_postgres_data

# Проверка прав доступа
ls -la /opt/fiscal-parser/
```

##### 3. Настройка SSH ключей:

```bash
# На пользователе деплоя создаем .ssh директорию
sudo su - fiskal_serbia_deploy
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавляем публичный ключ для авторизации GitHub Actions
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

##### 4. Настройка Docker (если не установлен):

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Запуск и включение Docker
sudo systemctl start docker
sudo systemctl enable docker

# Установка Docker Compose (если не установлен)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version  # Должна быть версия 2.24.6 или новее
```

##### 4.1. Создание .env файла на сервере:

```bash
# Переключиться на пользователя деплоя
sudo su - fiskal_serbia_deploy

# Перейти в директорию проекта
cd /opt/fiscal-parser

# Создать .env файл
nano .env

# Содержимое .env файла:
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=fiscal_data
POSTGRES_USER=fiscal_user
POSTGRES_PASSWORD=ваш_безопасный_пароль_для_бд
TG_TOKEN=ваш_токен_telegram_бота
ADMIN_ID=ваш_telegram_id
LOG_RETENTION_DAYS=30
DAILY_REQUEST_LIMIT=50

# Установить правильные права
chmod 600 .env
```

##### 5. GitHub Secrets для автоматического деплоя:

Добавьте в настройки репозитория GitHub → Settings → Secrets and variables → Actions:

```bash
# Обязательные секреты для деплоя
DEPLOY_HOST=your_server_ip              # IP адрес или домен сервера
DEPLOY_USER=fiskal_serbia_deploy        # Пользователь для SSH (как создали выше)
DEPLOY_SSH_KEY=your_private_ssh_key     # Приватный SSH ключ (полное содержимое)

# Пример DEPLOY_SSH_KEY:
# -----BEGIN OPENSSH PRIVATE KEY-----
# b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
# ...
# -----END OPENSSH PRIVATE KEY-----
```

##### 6. Проверка настроек:

```bash
# Проверка прав на папки
ls -la /opt/fiscal-parser/
ls -la /opt/fiscal-parser/log/

# Проверка Docker (от пользователя fiskal_serbia_deploy)
sudo su - fiskal_serbia_deploy
docker --version
docker-compose --version
docker ps  # Проверка доступа к Docker

# Проверка SSH подключения (с GitHub Actions)
ssh fiskal_serbia_deploy@your_server_ip "echo 'SSH connection successful'"
ssh fiskal_serbia_deploy@your_server_ip "docker ps"  # Проверка Docker через SSH
```

##### 6.1. Быстрое исправление прав (если деплой не работает):

```bash
# Выполните эти команды на сервере для исправления прав
sudo chown -R fiskal_serbia_deploy:fiskal_serbia_deploy /opt/fiscal-parser
sudo chmod -R 755 /opt/fiscal-parser
sudo usermod -aG docker fiskal_serbia_deploy

# Проверка
sudo su - fiskal_serbia_deploy
groups  # Должна быть группа docker
ls -la /opt/fiscal-parser/  # Должен быть владельцем

# Создание .env файла (если не существует)
cd /opt/fiscal-parser
if [ ! -f .env ]; then
  cp env_example.txt .env
  chmod 600 .env
  echo "Создан .env файл. Отредактируйте его с вашими значениями:"
  echo "TG_TOKEN=ваш_реальный_токен_бота"
  echo "ADMIN_ID=ваш_реальный_telegram_id"
  echo "POSTGRES_PASSWORD=ваш_безопасный_пароль"
  nano .env
fi
```

##### 7. Процесс автоматического деплоя:

CI автоматически выполняет следующие действия при push в main:

1. **Сохранение .env файла**: Резервное копирование существующего .env в /tmp/.env.backup
2. **Остановка существующих сервисов**: `docker-compose down --remove-orphans`
3. **Обновление кода**: Клонирование нового кода в /opt/fiscal-parser
4. **Восстановление .env файла**: Автоматическое восстановление из /tmp/.env.backup
5. **Создание .env из шаблона** (если файл не найден): Копирование env_example.txt → .env
6. **Сборка новых образов**: `docker-compose build --no-cache --pull`
7. **Запуск сервисов**: Попытка через `docker-compose up -d` или ручной запуск через `docker run`
8. **Проверка статуса**: Вывод статуса всех контейнеров
9. **Очистка ресурсов**: `docker system prune -f --volumes`

> **💡 Совет**: После первого деплоя проверьте логи: `docker-compose logs bot -f`
> **✅ Безопасность**: `.env` файл автоматически сохраняется и восстанавливается при каждом деплое
> **⚠️ Важно**: Если .env файл не найден, создается базовый из env_example.txt - отредактируйте его!
> **🔧 Совместимость**: docker-compose.yml адаптирован под версию 2.24.6, но Docker Compose 1.29.2 имеет проблемы с Docker API

**Подробнее**: `.github/workflows/README.md`

## 🧪 Тестирование

### Статус тестов: ✅ 284 теста проходят без ошибок

### Запуск тестов
```bash
# Установка зависимостей для тестов
pip install pytest pytest-asyncio pytest-mock pytest-cov

# Запуск всех тестов
pytest

# Тесты с подробным выводом
pytest -v

# Тесты с покрытием кода
pytest --cov=src --cov-report=html --cov-report=term-missing

# Запуск конкретных тестов
pytest tests/test_models.py -v
pytest tests/test_database_manager.py -v
```

### Структура тестов
- `tests/test_models.py` - ✅ Тесты Pydantic моделей
- `tests/test_database_manager.py` - ✅ Тесты менеджера БД (37 тестов, 90%+ покрытие)
- `tests/test_db_utils.py` - ✅ Тесты утилит базы данных
- `tests/test_parser.py` - ✅ Тесты парсера с Selenium
- `tests/test_bot_commands.py` - ✅ Тесты пользовательских команд
- `tests/test_admin_commands.py` - ✅ Тесты админских команд
- `tests/test_telegram_bot.py` - ✅ Тесты телеграм бота
- `tests/test_log_manager.py` - ✅ Тесты менеджера логов
- `tests/test_integration.py` - ✅ Интеграционные тесты
- `tests/conftest.py` - Фикстуры и настройки

### Покрытие тестами
- **Общее покрытие**: 90%+
- **База данных**: 95%+ (все публичные методы `DatabaseManager`)
- **Парсер**: 85%+ (включая обработку ошибок)
- **Логирование**: 90%+ (включая ротацию и очистку)
- **Телеграм бот**: 80%+ (включая админ команды)

### Makefile команды
```bash
make test           # Все тесты
make test-coverage  # С покрытием кода и HTML отчетом
make test-fast      # Только быстрые тесты
make test-models    # Только тесты моделей
make test-db        # Только тесты базы данных
make lint          # Линтинг кода
make clean-test     # Очистка тестовых файлов
```

### Конфигурация pytest
- **Warnings**: Отключены через `pytest.ini` для чистого вывода
- **Async поддержка**: Полная поддержка `pytest-asyncio`
- **Мокирование**: Комплексное мокирование зависимостей (psutil, Selenium, БД)
- **Fixtures**: Автоматическая настройка окружения и очистка


## 📚 Документация

- `tests/TESTING_GUIDE.md` - полное руководство по тестированию
- `requirements.txt` - основные зависимости
- `tests/requirements-test.txt` - зависимости для тестов
- `pytest.ini` - конфигурация pytest и покрытия
- `.coveragerc` - настройки анализа покрытия кода
- `Makefile` - автоматизированные команды разработки

## Пример

- **@ConvertingChekSerbianToRussiaBot**
