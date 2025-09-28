# Makefile для проекта Web_parsing_to_JSON_Serbia_fiskal

.PHONY: help install test test-unit test-integration test-coverage lint format clean docker-test

# Цель по умолчанию
help:
	@echo "Доступные команды:"
	@echo "  install         - Установить зависимости"
	@echo "  install-test    - Установить зависимости для тестирования"
	@echo "  test            - Запустить все тесты"
	@echo "  test-unit       - Запустить только unit тесты"
	@echo "  test-integration - Запустить только интеграционные тесты"
	@echo "  test-coverage   - Запустить тесты с отчетом о покрытии"
	@echo "  test-fast       - Запустить только быстрые тесты (пропустить медленные)"
	@echo "  lint           - Запустить проверки линтера"
	@echo "  format         - Форматировать код"
	@echo "  clean          - Очистить временные файлы"
	@echo "  docker-test    - Запустить тесты в Docker"

# Установка
install:
	pip install -r requirements.txt

install-test:
	pip install -r tests/requirements-test.txt

install-all: install install-test

# Тестирование
test:
	pytest

test-unit:
	pytest -m "not integration and not slow"

test-integration:
	pytest -m "integration"

test-fast:
	pytest -m "not slow"

test-slow:
	pytest -m "slow"

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing

test-coverage-xml:
	pytest --cov=src --cov-report=xml

# Конкретные категории тестов
test-models:
	pytest tests/test_models.py -v

test-db:
	pytest tests/test_db_utils.py -v

test-parser:
	pytest tests/test_parser.py -v

test-bot:
	pytest tests/test_bot_commands.py -v

test-log-manager:
	pytest tests/test_log_manager.py -v

# Параллельное тестирование
test-parallel:
	pytest -n auto

# Тестирование с разными уровнями подробности
test-verbose:
	pytest -v

test-quiet:
	pytest -q

# Линтинг и форматирование
lint:
	flake8 src tests
	mypy src --ignore-missing-imports
	bandit -r src

format:
	black src tests
	isort src tests

format-check:
	black --check src tests
	isort --check-only src tests

# Очистка
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/

# Docker тестирование
docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-test-clean:
	docker-compose -f docker-compose.test.yml down --volumes --remove-orphans

# Настройка разработки
dev-setup: install-all
	pre-commit install

# Настройка базы данных для тестирования
test-db-setup:
	docker-compose up -d postgres

test-db-teardown:
	docker-compose down postgres

# Генерация отчетов тестов
test-report:
	pytest --html=tests/reports/report.html --self-contained-html

test-junit:
	pytest --junit-xml=tests/reports/junit.xml

# Бенчмарк тесты
test-benchmark:
	pytest --benchmark-only

# Тесты безопасности
test-security:
	bandit -r src -f json -o tests/reports/security.json

# Профилирование производительности
test-profile:
	pytest --profile

# Тестирование конкретных компонентов с повторными попытками
test-retry:
	pytest --maxfail=3 --tb=short

# Тесты для конкретных окружений
test-local:
	TESTING=true pytest

test-ci:
	pytest --maxfail=1 --disable-warnings --tb=line

# Валидация тестовых данных
test-validate:
	pytest tests/test_models.py::TestModelValidation -v

# Тестирование обработки ошибок
test-errors:
	pytest -k "error" -v

# Тесты памяти и производительности
test-memory:
	pytest --memprof

# Тестирование с разными версиями Python (если используется tox)
test-py39:
	tox -e py39

test-py310:
	tox -e py310

test-py311:
	tox -e py311

# Тесты документации
test-docs:
	pytest --doctest-modules src/

# Генерация значка покрытия
coverage-badge:
	coverage-badge -o coverage.svg

# Полный набор тестов для CI/CD
test-full: clean install-test test-coverage lint

# Быстрый дымовой тест
smoke-test:
	pytest tests/test_models.py::TestSerbianItem::test_valid_item_creation -v
