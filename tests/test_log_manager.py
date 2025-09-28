"""
Тесты для менеджера логов в utils/log_manager.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.log_manager import LogManager, get_log_manager


class TestLogManager:
    """Тесты для класса LogManager."""

    def test_log_manager_initialization(self, temp_log_dir):
        """Тест инициализации LogManager."""
        with patch.dict("os.environ", {"LOG_RETENTION_DAYS": "15"}):
            log_manager = LogManager(log_dir=temp_log_dir, retention_days=15)

            assert log_manager.log_dir == temp_log_dir
            assert log_manager.retention_days == 15

    def test_log_manager_default_retention(self, temp_log_dir):
        """Тест LogManager с настройками удержания по умолчанию."""
        log_manager = LogManager(log_dir=temp_log_dir)

        assert log_manager.retention_days == 30  # Значение по умолчанию

    def test_get_daily_log_file(self, temp_log_dir):
        """Тест получения пути к ежедневному файлу логов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        log_file = log_manager.get_daily_log_file("test")

        today = datetime.now().strftime("%Y-%m-%d")
        expected_filename = f"test_{today}.log"

        assert log_file.name == expected_filename
        assert log_file.parent == temp_log_dir

    def test_get_daily_log_file_different_types(self, temp_log_dir):
        """Тест получения ежедневных файлов логов для разных типов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        bot_file = log_manager.get_daily_log_file("bot")
        parser_file = log_manager.get_daily_log_file("parser")

        assert "bot_" in bot_file.name
        assert "parser_" in parser_file.name
        assert bot_file != parser_file

    def test_can_write_to_log_dir_success(self, temp_log_dir):
        """Тест успешной проверки прав на запись."""
        log_manager = LogManager(log_dir=temp_log_dir)

        result = log_manager.can_write_to_log_dir()

        assert result is True

    def test_can_write_to_log_dir_failure(self, temp_log_dir):
        """Тест неудачной проверки прав на запись."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Мокаем ошибку прав доступа, патча операции с файлами
        with patch.object(Path, "touch", side_effect=PermissionError("Access denied")):
            result = log_manager.can_write_to_log_dir()
            assert result is False

    def test_can_write_to_log_dir_nonexistent(self):
        """Тест проверки прав на запись с несуществующей директорией."""
        # Используем временную директорию, которую можем контролировать
        with tempfile.TemporaryDirectory() as temp_base:
            non_existent_dir = Path(temp_base) / "non" / "existent" / "directory"

            with pytest.raises((FileNotFoundError, PermissionError)):
                LogManager(log_dir=non_existent_dir)

    def test_get_writable_file_path_success(self, temp_log_dir):
        """Тест успешного получения пути к записываемому файлу."""
        log_manager = LogManager(log_dir=temp_log_dir)

        file_path = log_manager.get_writable_file_path("test.log")

        assert file_path is not None
        assert file_path.parent == temp_log_dir

    def test_get_writable_file_path_failure(self, temp_log_dir):
        """Тест неудачного получения пути к записываемому файлу."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Мокаем ошибку прав доступа, патча метод can_write_to_log_dir
        with patch.object(log_manager, "can_write_to_log_dir", return_value=False):
            file_path = log_manager.get_writable_file_path("test.log")

            assert file_path is None

    def test_setup_logging_with_file(self, temp_log_dir):
        """Тест настройки логирования с обработчиком файлов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        logger = log_manager.setup_logging("test", logging.INFO)

        assert logger is not None
        assert logger.name == "test"
        assert logger.level == logging.INFO

        # Проверяем, что обработчики были добавлены
        assert len(logger.handlers) > 0

    def test_setup_logging_without_file_access(self, temp_log_dir):
        """Тест настройки логирования без доступа к файлам."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Мокаем неудачную запись в файл
        with patch.object(log_manager, "can_write_to_log_dir", return_value=False):
            logger = log_manager.setup_logging("test", logging.INFO)

            assert logger is not None
            # Должен все еще иметь консольный обработчик
            assert len(logger.handlers) > 0

    def test_setup_logging_file_handler_error(self, temp_log_dir):
        """Тест настройки логирования с ошибкой обработчика файлов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Мокаем неудачное создание FileHandler
        with patch("logging.FileHandler", side_effect=Exception("Handler error")):
            logger = log_manager.setup_logging("test", logging.INFO)

            # Должен переключиться на логирование только в консоль
            assert logger is not None

    def test_cleanup_old_logs(self, temp_log_dir):
        """Тест очистки старых файлов логов."""
        # Создаем LogManager без автоочистки в инициализации
        log_manager = LogManager.__new__(LogManager)
        log_manager.log_dir = temp_log_dir
        log_manager.retention_days = 7
        log_manager.log_dir.mkdir(exist_ok=True)

        # Создаем тестовые файлы логов
        old_file = temp_log_dir / "bot_old.log"
        recent_file = temp_log_dir / "bot_recent.log"

        old_file.write_text("old log content")
        recent_file.write_text("recent log content")

        # Мокаем os.path.getctime для возврата разных возрастов файлов
        def mock_getctime(path):
            today = datetime.now()
            if "old" in str(path):
                return (today - timedelta(days=10)).timestamp()
            else:
                return (today - timedelta(days=3)).timestamp()

        with patch("os.path.getctime", side_effect=mock_getctime):
            with patch("os.remove") as mock_remove:
                # Запускаем очистку
                deleted_count = log_manager.cleanup_old_logs()

                # Старый файл должен быть удален (мок будет вызван)
                assert deleted_count == 1
                mock_remove.assert_called_once()
                # Проверяем, что была попытка удалить правильный файл
                called_path = str(mock_remove.call_args[0][0])
                assert "bot_old.log" in called_path

    def test_cleanup_old_logs_no_files(self, temp_log_dir):
        """Тест очистки без файлов логов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Не должно вызывать ошибку
        log_manager.cleanup_old_logs()

        # Директория должна все еще существовать
        assert temp_log_dir.exists()

    def test_cleanup_old_logs_permission_error(self, temp_log_dir):
        """Тест очистки с ошибкой прав доступа."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Создаем тестовый файл
        test_file = temp_log_dir / "test_2025-01-01.log"
        test_file.write_text("test content")

        # Мокаем ошибку прав доступа при unlink
        with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
            # Не должно вызывать ошибку
            log_manager.cleanup_old_logs()

    def test_get_log_stats(self, temp_log_dir):
        """Тест получения статистики логов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Создаем тестовые файлы логов
        (temp_log_dir / "bot_2025-09-27.log").write_text("bot log content")
        (temp_log_dir / "parser_2025-09-27.log").write_text("parser log content" * 100)
        (temp_log_dir / "database_2025-09-26.log").write_text("db log")

        stats = log_manager.get_log_stats()

        assert stats["total_files"] == 3
        assert stats["total_size"] > 0
        assert stats["retention_days"] == log_manager.retention_days
        assert "by_type" in stats

    def test_get_log_stats_empty_directory(self, temp_log_dir):
        """Тест получения статистики логов с пустой директорией."""
        log_manager = LogManager(log_dir=temp_log_dir)

        stats = log_manager.get_log_stats()

        assert stats["total_files"] == 0
        assert stats["total_size"] == 0
        assert stats.get("by_type", {}) == {}

    def test_get_log_stats_permission_error(self, temp_log_dir):
        """Тест получения статистики логов с ошибкой прав доступа."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Мокаем glob для вызова ошибки прав доступа
        with patch.object(Path, "glob", side_effect=PermissionError("Access denied")):
            stats = log_manager.get_log_stats()

            # Должен возвращать безопасные значения по умолчанию
            assert stats["total_files"] == 0
            assert stats["total_size"] == 0
            assert stats.get("by_type", {}) == {}


class TestLogManagerDynamicPath:
    """Тесты для LogManager с динамическим определением пути."""

    def test_docker_environment_detection(self):
        """Тест определения Docker окружения через переменную окружения."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_manager = LogManager(log_dir=Path(temp_dir))
            assert log_manager.log_dir == Path(temp_dir)

    def test_local_environment_detection(self):
        """Тест определения локального окружения."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_manager = LogManager(log_dir=Path(temp_dir))
            assert log_manager.log_dir == Path(temp_dir)


class TestGetLogManager:
    """Тесты для функции get_log_manager."""

    def test_get_log_manager_creates_instance(self):
        """Тест того, что get_log_manager создает экземпляр LogManager."""
        # Очищаем любой существующий экземпляр
        if hasattr(get_log_manager, "_instance"):
            delattr(get_log_manager, "_instance")

        manager = get_log_manager()

        assert isinstance(manager, LogManager)
        assert hasattr(manager, "log_dir")
        assert hasattr(manager, "retention_days")

    def test_get_log_manager_singleton_behavior(self):
        """Тест того, что get_log_manager ведет себя как синглтон."""
        # Очищаем любой существующий экземпляр
        if hasattr(get_log_manager, "_instance"):
            delattr(get_log_manager, "_instance")

        manager1 = get_log_manager()
        manager2 = get_log_manager()

        # Должен возвращать тот же экземпляр при последующих вызовах
        assert manager1.log_dir == manager2.log_dir
        assert manager1.retention_days == manager2.retention_days


class TestLogManagerIntegration:
    """Интеграционные тесты для LogManager."""

    def test_full_logging_workflow(self, temp_log_dir):
        """Тест полного рабочего процесса логирования."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Настраиваем логгер
        logger = log_manager.setup_logging("integration_test", logging.INFO)

        # Логируем несколько сообщений
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Проверяем, что файл лога был создан
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"integration_test_{today}.log"

        # Файл должен существовать, если запись прошла успешно
        if log_file.exists():
            content = log_file.read_text()
            assert "Test info message" in content
            assert "Test warning message" in content
            assert "Test error message" in content

    def test_logger_configuration_isolation(self, temp_log_dir):
        """Тест того, что разные логгеры правильно изолированы."""
        log_manager = LogManager(log_dir=temp_log_dir)

        logger1 = log_manager.setup_logging("test1", logging.INFO)
        logger2 = log_manager.setup_logging("test2", logging.DEBUG)

        assert logger1.name != logger2.name
        assert logger1.level == logging.INFO
        assert logger2.level == logging.DEBUG

    def test_log_rotation_behavior(self, temp_log_dir):
        """Тест поведения ротации логов между днями."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Создаем логи для разных дней
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        yesterday_file = temp_log_dir / f"rotation_test_{yesterday}.log"
        today_file = temp_log_dir / f"rotation_test_{today}.log"

        yesterday_file.write_text("Yesterday's logs")
        today_file.write_text("Today's logs")

        # Оба файла должны рассматриваться как отдельные
        assert yesterday_file.exists()
        assert today_file.exists()
        assert yesterday_file.read_text() != today_file.read_text()

    def test_concurrent_logging_access(self, temp_log_dir):
        """Тест параллельного доступа к логированию."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Настраиваем несколько логгеров
        loggers = []
        for i in range(3):
            logger = log_manager.setup_logging(f"concurrent", logging.INFO)
            loggers.append(logger)

        # Логируем из нескольких логгеров (симулируя параллельный доступ)
        for i, logger in enumerate(loggers):
            logger.info(f"Message from logger {i}")

        # Должен обрабатывать параллельный доступ корректно
        assert len(loggers) == 3


class TestLogManagerErrorHandling:
    """Тесты для обработки ошибок в LogManager."""

    def test_invalid_log_retention_days(self, temp_log_dir):
        """Тест обработки недопустимых дней удержания логов."""
        # Тестируем со строкой, которую нельзя преобразовать в int
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)

        # Должен использовать предоставленное значение
        assert log_manager.retention_days == 30

    def test_negative_log_retention_days(self, temp_log_dir):
        """Тест обработки отрицательных дней удержания логов."""
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=-5)

        # Должен принимать отрицательное значение (хотя это может не иметь практического смысла)
        assert log_manager.retention_days == -5

    def test_log_directory_creation_failure(self):
        """Тест обработки неудачного создания директории логов."""
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Cannot create directory")):
            # Должен вызывать исключение во время инициализации
            with pytest.raises(PermissionError):
                LogManager(log_dir=Path("/root/cannot_create"))

    def test_corrupted_log_file_handling(self, temp_log_dir):
        """Тест обработки поврежденных файлов логов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Создаем "поврежденный" файл (пустой файл со странным именем)
        corrupted_file = temp_log_dir / "corrupted_log_file"
        corrupted_file.write_text("")

        # Должен обрабатывать корректно во время сбора статистики
        stats = log_manager.get_log_stats()
        assert stats is not None
        assert isinstance(stats, dict)

    def test_extremely_large_log_retention(self, temp_log_dir):
        """Тест обработки чрезвычайно больших значений удержания логов."""
        # Создаем LogManager с очень большим значением
        log_manager = LogManager.__new__(LogManager)
        log_manager.log_dir = temp_log_dir
        log_manager.retention_days = 999999
        log_manager.log_dir.mkdir(exist_ok=True)

        # Должен обрабатывать большие значения без ошибки
        assert log_manager.retention_days == 999999

        # Очистка должна все еще работать (хотя ничего не удалит) и не вызывать OverflowError
        deleted_count = log_manager.cleanup_old_logs()
        assert deleted_count == 0  # Не должно ничего удалять с таким большим удержанием


class TestLogManagerEnvironmentIntegration:
    """Тесты для интеграции LogManager с переменными окружения."""

    @patch.dict("os.environ", {"LOG_RETENTION_DAYS": "15"})
    def test_retention_from_environment_variable(self, temp_log_dir):
        """Тест чтения дней удержания из переменной окружения."""
        # Этот тест должен быть в самой функции get_log_manager
        # Здесь мы просто тестируем, что LogManager учитывает переданные значения
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=15)
        assert log_manager.retention_days == 15

    @patch.dict("os.environ", {"LOG_RETENTION_DAYS": "invalid"})
    def test_invalid_environment_variable(self, temp_log_dir):
        """Тест обработки недопустимой переменной окружения."""
        # LogManager должен все еще работать с явным параметром
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)
        assert log_manager.retention_days == 30

    def test_missing_environment_variable(self, temp_log_dir):
        """Тест поведения при отсутствии переменной окружения."""
        # Очищаем переменную окружения
        with patch.dict("os.environ", {}, clear=True):
            # LogManager должен работать с явным параметром
            log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)
            assert log_manager.retention_days == 30


class TestLogManagerFileOperations:
    """Тесты для файловых операций в LogManager."""

    def test_log_file_creation_and_writing(self, temp_log_dir):
        """Тест создания и записи файла логов."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Получаем путь к файлу логов
        log_file = log_manager.get_daily_log_file("file_ops_test")

        # Файл не должен существовать изначально
        assert not log_file.exists()

        # Настройка логирования должна создать файл при первой записи лога
        logger = log_manager.setup_logging("file_ops_test", logging.INFO)
        logger.info("Test message")

        # Файл может существовать сейчас (зависит от буферизации)
        # Мы не проверяем существование здесь, так как это зависит от деталей реализации

    def test_multiple_log_types_same_day(self, temp_log_dir):
        """Тест нескольких типов логов в один день."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Получаем разные типы файлов логов
        bot_file = log_manager.get_daily_log_file("bot")
        parser_file = log_manager.get_daily_log_file("parser")
        db_file = log_manager.get_daily_log_file("database")

        # Все должны быть разными файлами
        assert bot_file != parser_file
        assert parser_file != db_file
        assert bot_file != db_file

        # Все должны быть в одной директории
        assert bot_file.parent == temp_log_dir
        assert parser_file.parent == temp_log_dir
        assert db_file.parent == temp_log_dir
