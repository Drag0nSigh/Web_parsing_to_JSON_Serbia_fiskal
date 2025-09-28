# 🧪 Руководство по тестированию проекта Web_parsing_to_JSON_Serbia_fiskal

Полный набор тестов для проекта парсинга сербских фискальных данных с использованием pytest.

## 📁 Структура тестов

```
tests/
├── __init__.py                 # Инициализация пакета тестов
├── conftest.py                 # Общие фикстуры и конфигурация
├── requirements-test.txt       # Зависимости для тестирования
├── test_models.py             # Тесты Pydantic моделей
├── test_db_utils.py           # Тесты функций базы данных
├── test_parser.py             # Тесты парсера
├── test_bot_commands.py       # Тесты команд бота
├── test_log_manager.py        # Тесты менеджера логов
├── test_integration.py        # Интеграционные тесты
├── test_admin_commands.py     # Тесты админских команд
├── test_user_commands.py      # Тесты пользовательских команд
├── test_telegram_bot.py       # Тесты Telegram бота
└── TESTING_GUIDE.md          # Документация тестов
```

## 🚀 Быстрый старт

### Установка зависимостей
```bash
# Основные зависимости проекта
pip install -r requirements.txt

# Зависимости для тестирования
pip install -r tests/requirements-test.txt

# Или через make
make install-test
```

### Запуск тестов
```bash
# Все тесты
pytest

# Только быстрые тесты
pytest -m "not slow"

# С покрытием кода
pytest --cov=src --cov-report=html

# Параллельное выполнение
pytest -n auto

# Через make
make test-fast
make test-coverage
make test-parallel
```

## 📊 Категории тестов

### 🔧 Unit тесты
Тестируют отдельные компоненты в изоляции:

```bash
# Тесты моделей
pytest tests/test_models.py -v

# Тесты базы данных
pytest tests/test_db_utils.py -v

# Тесты парсера
pytest tests/test_parser.py -v

# Тесты логгера
pytest tests/test_log_manager.py -v
```

### 🌐 Integration тесты
Тестируют взаимодействие компонентов:

```bash
# Интеграционные тесты
pytest tests/test_integration.py -v

# Тесты с маркером integration
pytest -m integration
```

### 🤖 Bot тесты
Тестируют функциональность Telegram бота:

```bash
# Тесты команд бота
pytest tests/test_bot_commands.py -v

# Тесты админских команд
pytest tests/test_admin_commands.py -v

# Тесты пользовательских команд
pytest tests/test_user_commands.py -v

# Тесты Telegram бота
pytest tests/test_telegram_bot.py -v
```

### 🐌 Slow тесты
Медленные тесты (парсинг, большие данные):

```bash
# Только медленные тесты
pytest -m slow

# Исключить медленные тесты
pytest -m "not slow"
```

## 🛠️ Фикстуры и моки

### Основные фикстуры (conftest.py)

- `temp_log_dir` - Временная директория для логов
- `mock_log_manager` - Мок менеджера логов
- `mock_database` - Мок базы данных
- `sample_serbian_data` - Образец сербских данных
- `sample_russian_data` - Образец российских данных
- `mock_selenium_driver` - Мок Selenium WebDriver
- `mock_telegram_update` - Мок Telegram Update
- `mock_telegram_context` - Мок Telegram Context

### Использование фикстур

```python
def test_example(temp_log_dir, mock_database):
    """Тест с использованием фикстур."""
    # temp_log_dir содержит Path к временной директории
    # mock_database содержит мок базы данных
    pass
```

## 📋 Маркеры тестов

### Доступные маркеры

- `@pytest.mark.slow` - Медленные тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.unit` - Unit тесты
- `@pytest.mark.selenium` - Тесты с Selenium
- `@pytest.mark.database` - Тесты с базой данных
- `@pytest.mark.async` - Асинхронные тесты

### Использование маркеров

```python
@pytest.mark.slow
@pytest.mark.selenium
def test_complex_parsing():
    """Медленный тест с Selenium."""
    pass
```

## 📈 Покрытие кода

### Генерация отчетов

```bash
# HTML отчет
pytest --cov=src --cov-report=html

# Терминальный отчет
pytest --cov=src --cov-report=term-missing

# XML отчет (для CI/CD)
pytest --cov=src --cov-report=xml

# Через make
make test-coverage
```

### Цели покрытия

- **Минимальное покрытие**: 80%
- **Желательное покрытие**: 90%+
- **Критические модули**: 95%+

### Исключения из покрытия

- Точки входа (`main.py`, `start_bot.py`)
- Конфигурационные файлы
- Миграции базы данных
- Сгенерированный код

## 🔍 Типы тестов по модулям

### test_models.py
- ✅ Валидация Pydantic моделей
- ✅ Конвертация данных Serbian → Russian
- ✅ Обработка edge cases
- ✅ Генерация уникальных ID
- ✅ Расчет НДС

### test_db_utils.py
- ✅ CRUD операции пользователей
- ✅ Логирование запросов
- ✅ Проверка лимитов
- ✅ Статистика пользователей
- ✅ Обработка ошибок базы данных

### test_parser.py
- ✅ Парсинг сербских чисел
- ✅ Извлечение Knockout.js данных
- ✅ Обработка HTML
- ✅ Selenium WebDriver управление
- ✅ Обработка ошибок парсинга

### test_bot_commands.py
- ✅ Админские команды
- ✅ Пользовательские команды
- ✅ Обработка сообщений
- ✅ Активация/деактивация пользователей
- ✅ Telegram API взаимодействие

### test_log_manager.py
- ✅ Ежедневные лог файлы
- ✅ Очистка старых логов
- ✅ Определение прав записи
- ✅ Статистика логов
- ✅ Настройка логгеров

### test_integration.py
- ✅ Полный workflow парсинга
- ✅ Интеграция компонентов
- ✅ Реальные сценарии использования
- ✅ Производительность
- ✅ Обработка ошибок

## ⚡ Производительность тестов

### Быстрое выполнение

```bash
# Только быстрые unit тесты
make test-fast

# Параллельное выполнение
make test-parallel

# Остановка на первой ошибке
pytest --maxfail=1
```

### Профилирование

```bash
# Время выполнения тестов
pytest --durations=10

# Профилирование памяти
pytest --memprof

# Бенчмарки
pytest --benchmark-only
```

## 🐳 Docker тестирование

### Docker Compose для тестов

```bash
# Запуск тестов в контейнере
make docker-test

# Очистка после тестов
make docker-test-clean
```

### Изолированная среда

- Отдельная база данных для тестов
- Изолированные логи
- Чистое окружение для каждого запуска

## 🔧 CI/CD интеграция

### GitHub Actions пример

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: make install-test
      - run: make test-coverage
      - run: make lint
```

### Отчеты для CI

```bash
# JUnit XML для Jenkins/GitLab
pytest --junit-xml=tests/reports/junit.xml

# JSON отчет
pytest --json-report --json-report-file=tests/reports/report.json
```

## 🛡️ Безопасность тестов

### Тестирование безопасности

```bash
# Проверка уязвимостей
bandit -r src

# Безопасность в тестах
pytest --security
```

### Безопасные тестовые данные

- Никаких реальных токенов
- Мок-данные для всех внешних API
- Изолированная тестовая база данных

## 📝 Написание тестов

### Лучшие практики

1. **Именование**: `test_function_name_scenario`
2. **Структура**: Arrange → Act → Assert
3. **Независимость**: Каждый тест изолирован
4. **Читаемость**: Понятные названия и комментарии

### Шаблон теста

```python
def test_function_name_success_scenario(fixture1, fixture2):
    """Тест function_name с успешным сценарием."""
    # Arrange
    input_data = "test input"
    expected_result = "expected output"
    
    # Act
    result = function_name(input_data)
    
    # Assert
    assert result == expected_result
```

### Тестирование исключений

```python
def test_function_raises_exception():
    """Тест что функция вызывает соответствующее исключение."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_name("invalid_input")
```

### Async тесты

```python
@pytest.mark.asyncio
async def test_async_function():
    """Тест асинхронной функции."""
    result = await async_function()
    assert result is not None
```

## 🎯 Цели качества

### Метрики качества

- **Покрытие кода**: ≥80%
- **Успешность тестов**: 100%
- **Время выполнения**: <5 минут для всех тестов
- **Стабильность**: Нет flaky тестов

### Мониторинг качества

```bash
# Отчет о покрытии
make test-coverage

# Отчет о производительности
make test-benchmark

# Отчет о безопасности
make test-security
```

## 🔍 Debugging тестов

### Отладка упавших тестов

```bash
# Подробный вывод ошибок
pytest --tb=long

# Остановка на первой ошибке
pytest -x

# Запуск конкретного теста
pytest tests/test_models.py::TestSerbianItem::test_valid_item_creation -v
```

### Логирование в тестах

```bash
# Включить логи во время тестов
pytest --log-cli-level=DEBUG

# Сохранить логи в файл
pytest --log-file=tests/debug.log
```

## 🚨 Troubleshooting

### Проблема: ImportError
**Решение:** Убедитесь что src/ в PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:src"
# или используйте conftest.py (уже настроено)
```

### Проблема: ValidationError в тестах моделей
**Решение:** Проверьте обязательные поля модели
```python
# Посмотрите все поля SerbianFiscalData
from models.fiscal_models import SerbianFiscalData
print(SerbianFiscalData.model_fields.keys())
```

### Проблема: Тесты работают локально, но не в CI
**Решение:** Проверьте переменные окружения и версии Python

## 📚 Дополнительные ресурсы

- [Pytest документация](https://docs.pytest.org/)
- [Coverage.py документация](https://coverage.readthedocs.io/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/) - валидация моделей

## 🤝 Участие в разработке

### Добавление новых тестов

1. Создайте тест в соответствующем файле
2. Используйте существующие фикстуры
3. Добавьте маркеры при необходимости
4. Обновите документацию

### Стандарты качества

- Все новые функции должны иметь тесты
- Покрытие новых модулей ≥90%
- Тесты должны проходить на всех поддерживаемых версиях Python
- Использование типизации в тестах приветствуется

## 🎯 Roadmap

- [ ] Добавить property-based тесты (Hypothesis)
- [ ] Интеграционные тесты с реальной БД
- [ ] Performance тесты  
- [ ] Smoke тесты для CI/CD
- [ ] Mutation тестирование

## 🔧 Конфигурация

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
addopts = --verbose --tb=short --color=yes
markers =
    slow: медленные тесты
    integration: интеграционные тесты
    unit: unit тесты
    selenium: тесты с Selenium
    database: тесты с базой данных
    async: асинхронные тесты
```

### .coveragerc
```ini
[run]
source = src
branch = True
fail_under = 80

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```