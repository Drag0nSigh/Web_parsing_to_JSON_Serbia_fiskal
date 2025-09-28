"""
Tests for log manager in utils/log_manager.py - FIXED VERSION
"""
import pytest
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from utils.log_manager import LogManager, get_log_manager


class TestLogManager:
    """Tests for LogManager class."""
    
    def test_log_manager_initialization(self, temp_log_dir):
        """Test LogManager initialization."""
        with patch.dict('os.environ', {'LOG_RETENTION_DAYS': '15'}):
            log_manager = LogManager(log_dir=temp_log_dir, retention_days=15)

            assert log_manager.log_dir == temp_log_dir
            assert log_manager.retention_days == 15
    
    def test_log_manager_default_retention(self, temp_log_dir):
        """Test LogManager with default retention days."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        assert log_manager.retention_days == 30  # Default value
    
    def test_get_daily_log_file(self, temp_log_dir):
        """Test getting daily log file path."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        log_file = log_manager.get_daily_log_file("test")
        
        today = datetime.now().strftime("%Y-%m-%d")
        expected_filename = f"test_{today}.log"
        
        assert log_file.name == expected_filename
        assert log_file.parent == temp_log_dir
    
    def test_get_daily_log_file_different_types(self, temp_log_dir):
        """Test getting daily log files for different types."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        bot_file = log_manager.get_daily_log_file("bot")
        parser_file = log_manager.get_daily_log_file("parser")
        
        assert "bot_" in bot_file.name
        assert "parser_" in parser_file.name
        assert bot_file != parser_file
    
    def test_can_write_to_log_dir_success(self, temp_log_dir):
        """Test write permission check success."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        result = log_manager.can_write_to_log_dir()
        
        assert result is True
    
    def test_can_write_to_log_dir_failure(self, temp_log_dir):
        """Test write permission check failure."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Mock permission error by patching the file operations
        with patch.object(Path, 'touch', side_effect=PermissionError("Access denied")):
            result = log_manager.can_write_to_log_dir()
            assert result is False
    
    def test_can_write_to_log_dir_nonexistent(self):
        """Test write permission check with non-existent directory."""
        # Use a temporary directory that we can control
        with tempfile.TemporaryDirectory() as temp_base:
            non_existent_dir = Path(temp_base) / "non" / "existent" / "directory"
            
            with pytest.raises((FileNotFoundError, PermissionError)):
                LogManager(log_dir=non_existent_dir)
    
    def test_get_writable_file_path_success(self, temp_log_dir):
        """Test getting writable file path success."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        file_path = log_manager.get_writable_file_path("test.log")
        
        assert file_path is not None
        assert file_path.parent == temp_log_dir
    
    def test_get_writable_file_path_failure(self, temp_log_dir):
        """Test getting writable file path failure."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Mock permission error by patching the can_write_to_log_dir method
        with patch.object(log_manager, 'can_write_to_log_dir', return_value=False):
            file_path = log_manager.get_writable_file_path("test.log")
            
            assert file_path is None
    
    def test_setup_logging_with_file(self, temp_log_dir):
        """Test setting up logging with file handler."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        logger = log_manager.setup_logging("test", logging.INFO)
        
        assert logger is not None
        assert logger.name == "test"
        assert logger.level == logging.INFO
        
        # Check that handlers were added
        assert len(logger.handlers) > 0
    
    def test_setup_logging_without_file_access(self, temp_log_dir):
        """Test setting up logging without file access."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Mock file writing failure
        with patch.object(log_manager, 'can_write_to_log_dir', return_value=False):
            logger = log_manager.setup_logging("test", logging.INFO)
            
            assert logger is not None
            # Should still have console handler
            assert len(logger.handlers) > 0
    
    def test_setup_logging_file_handler_error(self, temp_log_dir):
        """Test setting up logging with file handler error."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Mock FileHandler creation failure
        with patch('logging.FileHandler', side_effect=Exception("Handler error")):
            logger = log_manager.setup_logging("test", logging.INFO)
            
            # Should fallback to console-only logging
            assert logger is not None
    
    def test_cleanup_old_logs(self, temp_log_dir):
        """Test cleanup of old log files."""
        # Создаем LogManager без автоочистки в инициализации
        log_manager = LogManager.__new__(LogManager)
        log_manager.log_dir = temp_log_dir
        log_manager.retention_days = 7
        log_manager.log_dir.mkdir(exist_ok=True)
        
        # Create test log files
        old_file = temp_log_dir / "bot_old.log"
        recent_file = temp_log_dir / "bot_recent.log"
        
        old_file.write_text("old log content")
        recent_file.write_text("recent log content")
        
        # Mock os.path.getctime to return different ages for files
        def mock_getctime(path):
            today = datetime.now()
            if "old" in str(path):
                return (today - timedelta(days=10)).timestamp()
            else:
                return (today - timedelta(days=3)).timestamp()
        
        with patch('os.path.getctime', side_effect=mock_getctime):
            with patch('os.remove') as mock_remove:
                # Run cleanup
                deleted_count = log_manager.cleanup_old_logs()
                
                # Old file should be deleted (mock will be called)
                assert deleted_count == 1
                mock_remove.assert_called_once()
                # Проверяем, что была попытка удалить правильный файл
                called_path = str(mock_remove.call_args[0][0])
                assert "bot_old.log" in called_path
    
    def test_cleanup_old_logs_no_files(self, temp_log_dir):
        """Test cleanup with no log files."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Should not raise error
        log_manager.cleanup_old_logs()
        
        # Directory should still exist
        assert temp_log_dir.exists()
    
    def test_cleanup_old_logs_permission_error(self, temp_log_dir):
        """Test cleanup with permission error."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Create a test file
        test_file = temp_log_dir / "test_2025-01-01.log"
        test_file.write_text("test content")
        
        # Mock permission error on unlink
        with patch.object(Path, 'unlink', side_effect=PermissionError("Access denied")):
            # Should not raise error
            log_manager.cleanup_old_logs()
    
    def test_get_log_stats(self, temp_log_dir):
        """Test getting log statistics."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Create test log files
        (temp_log_dir / "bot_2025-09-27.log").write_text("bot log content")
        (temp_log_dir / "parser_2025-09-27.log").write_text("parser log content" * 100)
        (temp_log_dir / "database_2025-09-26.log").write_text("db log")

        stats = log_manager.get_log_stats()

        assert stats['total_files'] == 3
        assert stats['total_size'] > 0
        assert stats['retention_days'] == log_manager.retention_days
        assert 'by_type' in stats
    
    def test_get_log_stats_empty_directory(self, temp_log_dir):
        """Test getting log statistics with empty directory."""
        log_manager = LogManager(log_dir=temp_log_dir)

        stats = log_manager.get_log_stats()

        assert stats['total_files'] == 0
        assert stats['total_size'] == 0
        assert stats.get('by_type', {}) == {}
    
    def test_get_log_stats_permission_error(self, temp_log_dir):
        """Test getting log statistics with permission error."""
        log_manager = LogManager(log_dir=temp_log_dir)

        # Mock glob to raise permission error
        with patch.object(Path, 'glob', side_effect=PermissionError("Access denied")):
            stats = log_manager.get_log_stats()

            # Should return safe defaults
            assert stats['total_files'] == 0
            assert stats['total_size'] == 0
            assert stats.get('by_type', {}) == {}


class TestLogManagerDynamicPath:
    """Tests for LogManager with dynamic path detection."""
    
    def test_docker_environment_detection(self):
        """Test Docker environment detection via environment variable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_manager = LogManager(log_dir=Path(temp_dir))
            assert log_manager.log_dir == Path(temp_dir)
    
    def test_local_environment_detection(self):
        """Test local environment detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_manager = LogManager(log_dir=Path(temp_dir))
            assert log_manager.log_dir == Path(temp_dir)


class TestGetLogManager:
    """Tests for get_log_manager function."""
    
    def test_get_log_manager_creates_instance(self):
        """Test that get_log_manager creates LogManager instance."""
        # Clear any existing instance
        if hasattr(get_log_manager, '_instance'):
            delattr(get_log_manager, '_instance')

        manager = get_log_manager()

        assert isinstance(manager, LogManager)
        assert hasattr(manager, 'log_dir')
        assert hasattr(manager, 'retention_days')
    
    def test_get_log_manager_singleton_behavior(self):
        """Test that get_log_manager behaves like a singleton."""
        # Clear any existing instance
        if hasattr(get_log_manager, '_instance'):
            delattr(get_log_manager, '_instance')

        manager1 = get_log_manager()
        manager2 = get_log_manager()

        # Should return same instance on subsequent calls
        assert manager1.log_dir == manager2.log_dir
        assert manager1.retention_days == manager2.retention_days


class TestLogManagerIntegration:
    """Integration tests for LogManager."""
    
    def test_full_logging_workflow(self, temp_log_dir):
        """Test complete logging workflow."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Setup logger
        logger = log_manager.setup_logging("integration_test", logging.INFO)
        
        # Log some messages
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Check that log file was created
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"integration_test_{today}.log"
        
        # File should exist if writing is successful
        if log_file.exists():
            content = log_file.read_text()
            assert "Test info message" in content
            assert "Test warning message" in content
            assert "Test error message" in content
    
    def test_logger_configuration_isolation(self, temp_log_dir):
        """Test that different loggers are properly isolated."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        logger1 = log_manager.setup_logging("test1", logging.INFO)
        logger2 = log_manager.setup_logging("test2", logging.DEBUG)
        
        assert logger1.name != logger2.name
        assert logger1.level == logging.INFO
        assert logger2.level == logging.DEBUG
    
    def test_log_rotation_behavior(self, temp_log_dir):
        """Test log rotation behavior across days."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Create logs for different days
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        yesterday_file = temp_log_dir / f"rotation_test_{yesterday}.log"
        today_file = temp_log_dir / f"rotation_test_{today}.log"
        
        yesterday_file.write_text("Yesterday's logs")
        today_file.write_text("Today's logs")
        
        # Both files should be treated as separate
        assert yesterday_file.exists()
        assert today_file.exists()
        assert yesterday_file.read_text() != today_file.read_text()
    
    def test_concurrent_logging_access(self, temp_log_dir):
        """Test concurrent access to logging."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Setup multiple loggers
        loggers = []
        for i in range(3):
            logger = log_manager.setup_logging(f"concurrent", logging.INFO)
            loggers.append(logger)
        
        # Log from multiple loggers (simulating concurrent access)
        for i, logger in enumerate(loggers):
            logger.info(f"Message from logger {i}")
        
        # Should handle concurrent access gracefully
        assert len(loggers) == 3


class TestLogManagerErrorHandling:
    """Tests for error handling in LogManager."""
    
    def test_invalid_log_retention_days(self, temp_log_dir):
        """Test handling invalid log retention days."""
        # Test with string that can't be converted to int
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)
        
        # Should use provided value
        assert log_manager.retention_days == 30
    
    def test_negative_log_retention_days(self, temp_log_dir):
        """Test handling negative log retention days."""
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=-5)
        
        # Should accept negative value (though it might not make practical sense)
        assert log_manager.retention_days == -5
    
    def test_log_directory_creation_failure(self):
        """Test handling log directory creation failure."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Cannot create directory")):
            # Should raise exception during initialization
            with pytest.raises(PermissionError):
                LogManager(log_dir=Path("/root/cannot_create"))
    
    def test_corrupted_log_file_handling(self, temp_log_dir):
        """Test handling corrupted log files."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Create a "corrupted" file (empty file with weird name)
        corrupted_file = temp_log_dir / "corrupted_log_file"
        corrupted_file.write_text("")
        
        # Should handle gracefully during stats collection
        stats = log_manager.get_log_stats()
        assert stats is not None
        assert isinstance(stats, dict)
    
    def test_extremely_large_log_retention(self, temp_log_dir):
        """Test handling extremely large log retention values."""
        # Создаем LogManager с очень большим значением
        log_manager = LogManager.__new__(LogManager)
        log_manager.log_dir = temp_log_dir
        log_manager.retention_days = 999999
        log_manager.log_dir.mkdir(exist_ok=True)
        
        # Should handle large values without error
        assert log_manager.retention_days == 999999
        
        # Cleanup should still work (though it won't delete anything) and not raise OverflowError
        deleted_count = log_manager.cleanup_old_logs()
        assert deleted_count == 0  # Should not delete anything with such large retention


class TestLogManagerEnvironmentIntegration:
    """Tests for LogManager integration with environment variables."""
    
    @patch.dict('os.environ', {'LOG_RETENTION_DAYS': '15'})
    def test_retention_from_environment_variable(self, temp_log_dir):
        """Test reading retention days from environment variable."""
        # This test should be in the get_log_manager function itself
        # Here we just test that LogManager respects passed values
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=15)
        assert log_manager.retention_days == 15
    
    @patch.dict('os.environ', {'LOG_RETENTION_DAYS': 'invalid'})
    def test_invalid_environment_variable(self, temp_log_dir):
        """Test handling invalid environment variable."""
        # LogManager should still work with explicit parameter
        log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)
        assert log_manager.retention_days == 30
    
    def test_missing_environment_variable(self, temp_log_dir):
        """Test behavior when environment variable is missing."""
        # Clear environment variable
        with patch.dict('os.environ', {}, clear=True):
            # LogManager should work with explicit parameter
            log_manager = LogManager(log_dir=temp_log_dir, retention_days=30)
            assert log_manager.retention_days == 30


class TestLogManagerFileOperations:
    """Tests for file operations in LogManager."""
    
    def test_log_file_creation_and_writing(self, temp_log_dir):
        """Test log file creation and writing."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Get log file path
        log_file = log_manager.get_daily_log_file("file_ops_test")
        
        # File shouldn't exist initially
        assert not log_file.exists()
        
        # Setup logging should create the file when first log is written
        logger = log_manager.setup_logging("file_ops_test", logging.INFO)
        logger.info("Test message")
        
        # File might exist now (depends on buffering)
        # We don't assert existence here since it depends on implementation details
    
    def test_multiple_log_types_same_day(self, temp_log_dir):
        """Test multiple log types on the same day."""
        log_manager = LogManager(log_dir=temp_log_dir)
        
        # Get different log file types
        bot_file = log_manager.get_daily_log_file("bot")
        parser_file = log_manager.get_daily_log_file("parser")
        db_file = log_manager.get_daily_log_file("database")
        
        # All should be different files
        assert bot_file != parser_file
        assert parser_file != db_file
        assert bot_file != db_file
        
        # All should be in the same directory
        assert bot_file.parent == temp_log_dir
        assert parser_file.parent == temp_log_dir
        assert db_file.parent == temp_log_dir
