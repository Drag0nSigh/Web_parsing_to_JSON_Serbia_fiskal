# Зависимости проекта

## Файлы зависимостей

- **`requirements.txt`** - Основные зависимости для работы приложения
- **`tests/requirements-test.txt`** - Зависимости для тестирования
- **`requirements-dev.txt`** - Все зависимости для разработки (основные + тестовые)
- **`requirements-freeze.txt`** - Точные версии всех установленных пакетов

## Установка

### Для работы приложения:
```bash
pip install -r requirements.txt
```

### Для разработки:
```bash
pip install -r requirements-dev.txt
```

### Только тестирование:
```bash
pip install -r tests/requirements-test.txt
```

## Python 3.13

Проект настроен для работы с **Python 3.13**. Все зависимости совместимы с этой версией.

## Важные замечания

- **pytest-postgresql**: Используется версия 3.1.3 (совместима с psycopg2-binary)
- **setuptools**: Требуется для Python 3.13 (включен в requirements.txt)
- **psycopg2-binary**: Используется вместо psycopg3 для совместимости

## Тестирование

Все тесты проходят успешно:
```bash
pytest tests/ -v
```

**Результат**: 284 теста - все PASSED ✅
