"""
Tests for DatabaseManager in db/database.py
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from db.database import DatabaseManager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        with patch.object(DatabaseManager, "_setup_database") as mock_setup:
            DatabaseManager()
            mock_setup.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "POSTGRES_HOST": "test_host",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_DB": "test_db",
        },
    )
    @patch("db.database.create_engine")
    @patch("db.database.sessionmaker")
    def test_setup_database_with_env_vars(self, mock_sessionmaker, mock_create_engine):
        """Test database setup with environment variables."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_class = Mock()
        mock_sessionmaker.return_value = mock_session_class

        dm = DatabaseManager()

        expected_url = "postgresql://test_user:test_pass@test_host:5432/test_db"
        mock_create_engine.assert_called_once_with(expected_url, echo=False, pool_pre_ping=True, pool_recycle=3600)
        mock_sessionmaker.assert_called_once_with(autocommit=False, autoflush=False, bind=mock_engine)

        assert dm.engine == mock_engine
        assert dm.SessionLocal == mock_session_class

    @patch.dict("os.environ", {"DATABASE_URL": "postgresql://user:pass@host:5432/db"})
    @patch("db.database.create_engine")
    @patch("db.database.sessionmaker")
    def test_setup_database_with_database_url(self, mock_sessionmaker, mock_create_engine):
        """Test database setup with DATABASE_URL."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        DatabaseManager()

        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@host:5432/db", echo=False, pool_pre_ping=True, pool_recycle=3600
        )

    @patch("db.database.create_engine")
    def test_setup_database_with_defaults(self, mock_create_engine):
        """Test database setup with default values."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Clear environment variables
        with patch.dict("os.environ", {}, clear=True):
            DatabaseManager()

        expected_url = "postgresql://fiscal_user:secure_password_123@localhost:5432/fiscal_data"
        mock_create_engine.assert_called_once_with(expected_url, echo=False, pool_pre_ping=True, pool_recycle=3600)

    @patch("db.database.create_engine")
    def test_setup_database_error(self, mock_create_engine):
        """Test database setup error handling."""
        mock_create_engine.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            DatabaseManager()

    @patch.object(DatabaseManager, "_setup_database")
    @patch("db.database.Base")
    def test_init_database_success(self, mock_base, mock_setup_db):
        """Test successful database initialization."""
        dm = DatabaseManager()
        dm.engine = Mock()

        result = dm.init_database()

        assert result is True
        mock_base.metadata.create_all.assert_called_once_with(bind=dm.engine)

    @patch.object(DatabaseManager, "_setup_database")
    @patch("db.database.Base")
    def test_init_database_error(self, mock_base, mock_setup_db):
        """Test database initialization error."""
        dm = DatabaseManager()
        dm.engine = Mock()
        mock_base.metadata.create_all.side_effect = Exception("Table creation failed")

        result = dm.init_database()

        assert result is False

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_session_success(self, mock_setup_db):
        """Test successful session context manager."""
        dm = DatabaseManager()
        mock_session = Mock()
        dm.SessionLocal = Mock(return_value=mock_session)

        with dm.get_session() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_session_error(self, mock_setup_db):
        """Test session context manager with error."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_session.commit.side_effect = Exception("Commit failed")
        dm.SessionLocal = Mock(return_value=mock_session)

        with pytest.raises(Exception, match="Commit failed"):
            with dm.get_session() as session:
                pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch.object(DatabaseManager, "_setup_database")
    @patch("db.database.text")
    def test_check_connection_success(self, mock_text, mock_setup_db):
        """Test successful connection check."""
        dm = DatabaseManager()
        mock_engine = Mock()
        mock_connection = Mock()

        # Правильно настраиваем контекстный менеджер
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_connection)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_context_manager

        dm.engine = mock_engine

        result = dm.check_connection()

        assert result is True
        mock_connection.execute.assert_called_once()
        mock_text.assert_called_once_with("SELECT 1")

    @patch.object(DatabaseManager, "_setup_database")
    def test_check_connection_error(self, mock_setup_db):
        """Test connection check error."""
        dm = DatabaseManager()
        mock_engine = Mock()
        mock_engine.connect.side_effect = Exception("Connection failed")
        dm.engine = mock_engine

        result = dm.check_connection()

        assert result is False

    @patch.object(DatabaseManager, "_setup_database")
    def test_create_or_update_user_new_user(self, mock_setup_db):
        """Test creating a new user."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.create_or_update_user(123, "test_user")

            assert result is not None
            mock_session.add.assert_called_once()

    @patch.object(DatabaseManager, "_setup_database")
    def test_create_or_update_user_existing_user(self, mock_setup_db):
        """Test updating an existing user."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_user = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.create_or_update_user(123, "updated_user")

            assert result == mock_user
            assert mock_user.username == "updated_user"
            assert isinstance(mock_user.last_activity, datetime)

    @patch.object(DatabaseManager, "_setup_database")
    def test_create_or_update_user_error(self, mock_setup_db):
        """Test user creation/update error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.create_or_update_user(123, "test_user")

            assert result is None

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_user_success(self, mock_setup_db):
        """Test successful user retrieval."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_user = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_user(123)

            assert result == mock_user

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_user_not_found(self, mock_setup_db):
        """Test user not found."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_user(123)

            assert result is None

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_user_error(self, mock_setup_db):
        """Test user retrieval error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_user(123)

            assert result is None

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_all_users_success(self, mock_setup_db):
        """Test successful retrieval of all users."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_users = [Mock(), Mock(), Mock()]
        query_mock = mock_session.query.return_value
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_users

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_all_users(limit=50, offset=10)

            assert result == mock_users
            query_mock.order_by.assert_called_once()
            query_mock.order_by.return_value.offset.assert_called_once_with(10)
            query_mock.order_by.return_value.offset.return_value.limit.assert_called_once_with(50)

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_all_users_error(self, mock_setup_db):
        """Test get all users error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_all_users()

            assert result == []

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_users_count_success(self, mock_setup_db):
        """Test successful users count."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_session.query.return_value.count.return_value = 42

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_users_count()

            assert result == 42

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_users_count_error(self, mock_setup_db):
        """Test users count error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_users_count()

            assert result == 0

    @patch.object(DatabaseManager, "_setup_database")
    def test_add_request_log_new_user(self, mock_setup_db):
        """Test adding request log for new user."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.add_request_log(123, "test_user", "success")

            assert result is not None
            # Проверяем, что добавили и пользователя, и лог
            assert mock_session.add.call_count == 2

    @patch.object(DatabaseManager, "_setup_database")
    def test_add_request_log_existing_user(self, mock_setup_db):
        """Test adding request log for existing user."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_user = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.add_request_log(123, "updated_user", "error", "Some error")

            assert result is not None
            assert mock_user.username == "updated_user"
            assert isinstance(mock_user.last_activity, datetime)
            # Проверяем, что добавили только лог (пользователь уже существовал)
            mock_session.add.assert_called_once()

    @patch.object(DatabaseManager, "_setup_database")
    def test_add_request_log_error(self, mock_setup_db):
        """Test add request log error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.add_request_log(123, "test_user")

            assert result is None

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_request_logs_with_filters(self, mock_setup_db):
        """Test getting request logs with all filters."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_logs = [Mock(), Mock()]

        # Создаем цепочку методов запроса
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_logs

        date_from = datetime(2025, 9, 1)
        date_to = datetime(2025, 9, 30)

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_request_logs(limit=20, offset=5, user_id=123, date_from=date_from, date_to=date_to)

            assert result == mock_logs
            # Проверяем, что filter был вызван 3 раза (user_id, date_from, date_to)
            assert query_mock.filter.call_count == 3

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_request_logs_no_filters(self, mock_setup_db):
        """Test getting request logs without filters."""
        dm = DatabaseManager()
        mock_session = Mock()
        mock_logs = [Mock()]

        query_mock = mock_session.query.return_value
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_logs

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_request_logs()

            assert result == mock_logs
            # Проверяем, что filter не был вызван
            query_mock.filter.assert_not_called()

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_request_logs_error(self, mock_setup_db):
        """Test get request logs error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_request_logs()

            assert result == []

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_request_logs_count_with_filters(self, mock_setup_db):
        """Test getting request logs count with filters."""
        dm = DatabaseManager()
        mock_session = Mock()

        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 15

        date_from = datetime(2025, 9, 1)
        date_to = datetime(2025, 9, 30)

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_request_logs_count(user_id=123, date_from=date_from, date_to=date_to)

            assert result == 15
            assert query_mock.filter.call_count == 3

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_request_logs_count_error(self, mock_setup_db):
        """Test get request logs count error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_request_logs_count()

            assert result == 0

    @patch.object(DatabaseManager, "_setup_database")
    @patch("db.database.datetime")
    def test_get_daily_stats_with_date(self, mock_datetime, mock_setup_db):
        """Test getting daily stats with specific date."""
        dm = DatabaseManager()
        mock_session = Mock()

        # Настройка моков для запросов
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 10
        query_mock.distinct.return_value.count.return_value = 5

        # Разные значения для разных запросов
        query_mock.count.side_effect = [10, 8, 5]

        test_date = datetime(2025, 9, 27).date()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_daily_stats(test_date)

            expected = {
                "date": "2025-09-27",
                "total_requests": 10,
                "successful_requests": 8,
                "failed_requests": 2,
                "unique_users": 5,
            }
            assert result == expected

    @patch.object(DatabaseManager, "_setup_database")
    @patch("db.database.datetime")
    def test_get_daily_stats_default_date(self, mock_datetime, mock_setup_db):
        """Test getting daily stats with default date (today)."""
        dm = DatabaseManager()
        mock_session = Mock()

        # Мокаем datetime.now().date()
        mock_today = datetime(2025, 9, 28).date()
        mock_datetime.now.return_value.date.return_value = mock_today
        mock_datetime.combine = datetime.combine
        mock_datetime.min = datetime.min
        mock_datetime.max = datetime.max

        # Настраиваем правильно моки для трех разных запросов
        def create_query_mock(count_value):
            query = Mock()
            query.filter.return_value = query
            query.count.return_value = count_value
            query.distinct.return_value.count.return_value = count_value
            return query

        # Создаем разные запросы для разных вызовов
        mock_session.query.side_effect = [
            create_query_mock(5),  # total_requests
            create_query_mock(3),  # successful_requests
            create_query_mock(2),  # unique_users
        ]

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = dm.get_daily_stats()

            assert result["date"] == "2025-09-28"
            assert result["total_requests"] == 5
            assert result["successful_requests"] == 3
            assert result["unique_users"] == 2

    @patch.object(DatabaseManager, "_setup_database")
    def test_get_daily_stats_error(self, mock_setup_db):
        """Test get daily stats error."""
        dm = DatabaseManager()

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database error")

            result = dm.get_daily_stats()

            assert result == {}

    @patch.object(DatabaseManager, "_setup_database")
    def test_close_with_engine(self, mock_setup_db):
        """Test closing connection with engine."""
        dm = DatabaseManager()
        mock_engine = Mock()
        dm.engine = mock_engine

        dm.close()

        mock_engine.dispose.assert_called_once()

    @patch.object(DatabaseManager, "_setup_database")
    def test_close_without_engine(self, mock_setup_db):
        """Test closing connection without engine."""
        dm = DatabaseManager()
        dm.engine = None

        # Should not raise error
        dm.close()


class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager."""

    @patch.object(DatabaseManager, "_setup_database")
    def test_full_user_workflow(self, mock_setup_db):
        """Test complete user workflow."""
        dm = DatabaseManager()
        mock_session = Mock()

        # Настройка для создания пользователя
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(dm, "get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Создаем пользователя
            user = dm.create_or_update_user(123, "test_user")
            assert user is not None

            # Добавляем лог запроса
            log = dm.add_request_log(123, "test_user", "success")
            assert log is not None

    def test_database_url_parsing(self):
        """Test URL parsing with different formats."""
        test_cases = [
            {"url": "postgresql://user:pass@host:5432/db", "expected_log": "host:5432/db"},
            {"url": "postgresql://user@host/db", "expected_log": "host/db"},
            {"url": "localhost:5432/db", "expected_log": "localhost"},
        ]

        for case in test_cases:
            with patch.dict("os.environ", {"DATABASE_URL": case["url"]}, clear=True):
                with patch("db.database.create_engine") as mock_create_engine:
                    with patch("db.database.sessionmaker"):
                        with patch("db.database.logger") as mock_logger:
                            DatabaseManager()

                            # Проверяем, что логирование произошло с правильным URL
                            log_calls = mock_logger.info.call_args_list
                            connection_log = next(
                                (call for call in log_calls if "Подключение к базе данных:" in str(call[0][0])), None
                            )
                            assert connection_log is not None
                            assert case["expected_log"] in str(connection_log)


class TestDatabaseManagerGlobalInstance:
    """Tests for global database manager instance."""

    def test_global_db_manager_exists(self):
        """Test that global db_manager instance exists."""
        from db.database import db_manager

        assert db_manager is not None
