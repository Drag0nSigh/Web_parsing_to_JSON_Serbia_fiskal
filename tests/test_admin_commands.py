"""
Тесты для админских команд в bot_tg/admin_commands.py
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest


# Мокируем переменные окружения перед импортом админских команд
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Мокировать переменные окружения для всех тестов."""
    with patch.dict(
        os.environ,
        {"ADMIN_ID": "123456789", "DAILY_REQUEST_LIMIT": "50", "TG_TOKEN": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    ):
        yield


# Импортируем модуль админских команд с правильной обработкой ошибок
try:
    from bot_tg.admin_commands import (
        activate_user_command,
        admin_logs,
        admin_logs_date,
        admin_start,
        admin_stats,
        admin_status,
        admin_test,
        admin_users,
        deactivate_user_command,
        format_datetime,
        is_admin,
        send_message_to_user,
    )
except ImportError as e:
    pytest.skip(f"Admin commands module not available: {e}", allow_module_level=True)


class TestFormatDatetime:
    """Тесты для функции format_datetime."""

    def test_format_datetime_valid_iso(self):
        """Тест форматирования валидной ISO строки datetime."""
        result = format_datetime("2025-09-28T15:30:45Z")
        assert result == "28.09.25 15:30:45"

    def test_format_datetime_valid_iso_with_timezone(self):
        """Тест форматирования валидной ISO строки datetime с часовым поясом."""
        result = format_datetime("2025-09-28T15:30:45+00:00")
        assert result == "28.09.25 15:30:45"

    def test_format_datetime_none(self):
        """Тест форматирования значения None."""
        result = format_datetime(None)
        assert result == "N/A"

    def test_format_datetime_empty_string(self):
        """Тест форматирования пустой строки."""
        result = format_datetime("")
        assert result == "N/A"

    def test_format_datetime_n_a(self):
        """Тест форматирования строки 'N/A'."""
        result = format_datetime("N/A")
        assert result == "N/A"

    def test_format_datetime_invalid_format(self):
        """Тест форматирования невалидной строки datetime."""
        result = format_datetime("invalid-date")
        assert result == "invalid-date"

    def test_format_datetime_attribute_error(self):
        """Тест форматирования с AttributeError."""
        result = format_datetime(123)  # Not a string
        assert result == 123


class TestIsAdmin:
    """Тесты для функции is_admin."""

    def test_is_admin_true(self):
        """Тест проверки админа для валидного ID админа."""
        assert is_admin(123456789) is True

    def test_is_admin_false(self):
        """Тест проверки админа для не-админского ID."""
        assert is_admin(987654321) is False

    def test_is_admin_zero(self):
        """Тест проверки админа для нулевого ID."""
        assert is_admin(0) is False


class TestAdminStart:
    """Тесты для admin_start command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_start_success(self, mock_update, mock_context):
        """Тест successful admin start command."""
        # Мокируем функцию create_admin_menu
        mock_admin_menu = Mock()

        with patch("bot_tg.telegram_bot.create_admin_menu", return_value=mock_admin_menu):
            await admin_start(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Административная панель" in call_args[0][0]
            assert call_args[1]["parse_mode"] == "HTML"
            assert call_args[1]["reply_markup"] == mock_admin_menu

    @pytest.mark.asyncio
    async def test_admin_start_not_admin(self, mock_update, mock_context):
        """Тест admin start command for non-admin user."""
        mock_update.effective_user.id = 987654321

        await admin_start(mock_update, mock_context)

        # Должно быть вызвано дважды: один раз для отладочного сообщения, один раз для ошибки
        assert mock_update.message.reply_text.call_count == 2
        call_args = mock_update.message.reply_text.call_args_list
        assert "нет прав администратора" in call_args[-1][0][0]


class TestAdminLogs:
    """Тесты для admin_logs command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_logs_success(self, mock_update, mock_context):
        """Тест successful admin logs command."""
        with patch("bot_tg.admin_commands.get_recent_logs") as mock_get_logs:
            mock_get_logs.return_value = [
                {
                    "created_at": "2025-09-28T15:30:45Z",
                    "user_id": 123456789,
                    "username": "test_user",
                    "status": "success",
                    "error_message": "",
                }
            ]

            await admin_logs(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Последние логи запросов" in call_args[0][0]
            assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_admin_logs_no_logs(self, mock_update, mock_context):
        """Тест admin logs command with no logs."""
        with patch("bot_tg.admin_commands.get_recent_logs") as mock_get_logs:
            mock_get_logs.return_value = []

            await admin_logs(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Логи не найдены" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_logs_with_errors(self, mock_update, mock_context):
        """Тест admin logs command with error logs."""
        with patch("bot_tg.admin_commands.get_recent_logs") as mock_get_logs:
            mock_get_logs.return_value = [
                {
                    "created_at": "2025-09-28T15:30:45Z",
                    "user_id": 123456789,
                    "username": "test_user",
                    "status": "error",
                    "error_message": "Test error message",
                }
            ]

            await admin_logs(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "❌" in call_args[0][0]  # Error emoji
            assert "Test error message" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_logs_exception(self, mock_update, mock_context):
        """Тест admin logs command with exception."""
        with patch("bot_tg.admin_commands.get_recent_logs") as mock_get_logs:
            mock_get_logs.side_effect = Exception("Database error")

            await admin_logs(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ошибка получения логов" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_logs_not_admin(self, mock_update, mock_context):
        """Тест admin logs command for non-admin user."""
        mock_update.effective_user.id = 987654321

        await admin_logs(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "нет прав администратора" in call_args[0][0]


class TestAdminLogsDate:
    """Тесты для admin_logs_date command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        update.message.text = "/admin_logs_28_09_25"
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_logs_date_success(self, mock_update, mock_context):
        """Тест successful admin logs date command."""
        with patch("bot_tg.admin_commands.get_request_logs") as mock_get_logs:
            mock_get_logs.return_value = [
                {
                    "created_at": "2025-09-28T15:30:45Z",
                    "user_id": 123456789,
                    "username": "test_user",
                    "status": "success",
                    "error_message": "",
                }
            ]

            await admin_logs_date(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Логи за 28_09_25" in call_args[0][0]
            assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_admin_logs_date_invalid_format(self, mock_update, mock_context):
        """Тест admin logs date command with invalid date format."""
        mock_update.message.text = "/admin_logs_invalid_date"

        await admin_logs_date(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Неверный формат даты" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_logs_date_no_logs(self, mock_update, mock_context):
        """Тест admin logs date command with no logs for date."""
        with patch("bot_tg.admin_commands.get_request_logs") as mock_get_logs:
            mock_get_logs.return_value = []

            await admin_logs_date(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Логи за 28_09_25 не найдены" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_logs_date_exception(self, mock_update, mock_context):
        """Тест admin logs date command with exception."""
        with patch("bot_tg.admin_commands.get_request_logs") as mock_get_logs:
            mock_get_logs.side_effect = Exception("Database error")

            await admin_logs_date(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ошибка получения логов за дату" in call_args[0][0]


class TestAdminUsers:
    """Тесты для admin_users command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_users_success(self, mock_update, mock_context):
        """Тест successful admin users command."""
        with patch("bot_tg.admin_commands.get_users_list") as mock_get_users:
            mock_get_users.return_value = [
                {
                    "telegram_id": 123456789,
                    "username": "test_user",
                    "created_at": "2025-09-28T15:30:45Z",
                    "last_activity": "2025-09-28T15:30:45Z",
                    "is_active": True,
                }
            ]

            await admin_users(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Список пользователей" in call_args[0][0]
            assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_admin_users_no_users(self, mock_update, mock_context):
        """Тест admin users command with no users."""
        with patch("bot_tg.admin_commands.get_users_list") as mock_get_users:
            mock_get_users.return_value = []

            await admin_users(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Пользователи не найдены" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_users_exception(self, mock_update, mock_context):
        """Тест admin users command with exception."""
        with patch("bot_tg.admin_commands.get_users_list") as mock_get_users:
            mock_get_users.side_effect = Exception("Database error")

            await admin_users(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ошибка получения пользователей" in call_args[0][0]


class TestAdminTest:
    """Тесты для admin_test command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_test_success(self, mock_update, mock_context):
        """Тест successful admin test command."""
        with patch("parser.fiscal_parser.parse_serbian_fiscal_url") as mock_parse:
            mock_parse.return_value = {"test": "data"}

            await admin_test(mock_update, mock_context)

            # Should be called twice: once for testing message, once for result
            assert mock_update.message.reply_text.call_count == 2
            call_args = mock_update.message.reply_text.call_args_list
            assert "Тестирую парсер" in call_args[0][0][0]
            assert "Парсер работает корректно" in call_args[1][0][0]

    @pytest.mark.asyncio
    async def test_admin_test_empty_result(self, mock_update, mock_context):
        """Тест admin test command with empty result."""
        with patch("parser.fiscal_parser.parse_serbian_fiscal_url") as mock_parse:
            mock_parse.return_value = []

            await admin_test(mock_update, mock_context)

            assert mock_update.message.reply_text.call_count == 2
            call_args = mock_update.message.reply_text.call_args_list
            assert "Парсер вернул пустой результат" in call_args[1][0][0]

    @pytest.mark.asyncio
    async def test_admin_test_exception(self, mock_update, mock_context):
        """Тест admin test command with exception."""
        with patch("parser.fiscal_parser.parse_serbian_fiscal_url") as mock_parse:
            mock_parse.side_effect = Exception("Parser error")

            await admin_test(mock_update, mock_context)

            assert mock_update.message.reply_text.call_count == 2
            call_args = mock_update.message.reply_text.call_args_list
            assert "Ошибка при тестировании" in call_args[1][0][0]


class TestAdminStatus:
    """Тесты для admin_status command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_status_success(self, mock_update, mock_context):
        """Тест successful admin status command."""
        # Мокируем psutil и platform модули
        mock_psutil = Mock()
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = Mock(percent=60, used=8 * 1024**3, total=16 * 1024**3)
        mock_psutil.disk_usage.return_value = Mock(percent=45, used=200 * 1024**3, total=500 * 1024**3)

        mock_platform = Mock()
        mock_platform.system.return_value = "Windows"
        mock_platform.release.return_value = "10"

        mock_log_manager = Mock()
        mock_log_manager.get_log_stats.return_value = {
            "total_files": 15,
            "total_size": 2560,  # 2.5 KB
            "retention_days": 30,
        }

        with patch.dict("sys.modules", {"psutil": mock_psutil, "platform": mock_platform}):
            with patch("utils.log_manager.get_log_manager", return_value=mock_log_manager):
                with patch("bot_tg.admin_commands.datetime") as mock_datetime:
                    mock_datetime.now.return_value.strftime.return_value = "28.09.25 15:00:00"

                    await admin_status(mock_update, mock_context)

                    mock_update.message.reply_text.assert_called_once()
                    call_args = mock_update.message.reply_text.call_args
                    assert "Статус системы" in call_args[0][0]
                    assert call_args[1]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_admin_status_exception(self, mock_update, mock_context):
        """Тест admin status command with exception."""
        # Мокируем psutil чтобы вызвать исключение
        mock_psutil = Mock()
        mock_psutil.cpu_percent.side_effect = Exception("System error")

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            await admin_status(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ошибка при получении статуса" in call_args[0][0]


class TestAdminStats:
    """Тесты для admin_stats command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_admin_stats_success(self, mock_update, mock_context):
        """Тест successful admin stats command."""
        with patch("bot_tg.admin_commands.get_system_stats") as mock_get_stats:
            with patch("bot_tg.admin_commands.get_database_info") as mock_get_db_info:
                mock_get_stats.return_value = {
                    "total_requests": 100,
                    "successful_requests": 95,
                    "failed_requests": 5,
                    "unique_users": 10,
                    "daily_stats": [{"date": "2025-09-28", "total_requests": 20, "unique_users": 5}],
                }
                mock_get_db_info.return_value = {"users_count": 10, "logs_count": 100, "connection_status": "connected"}

                await admin_stats(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Статистика использования" in call_args[0][0]
                assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_admin_stats_no_stats(self, mock_update, mock_context):
        """Тест admin stats command with no stats."""
        with patch("bot_tg.admin_commands.get_system_stats") as mock_get_stats:
            mock_get_stats.return_value = None

            await admin_stats(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Статистика недоступна" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_admin_stats_exception(self, mock_update, mock_context):
        """Тест admin stats command with exception."""
        with patch("bot_tg.admin_commands.get_system_stats") as mock_get_stats:
            mock_get_stats.side_effect = Exception("Database error")

            await admin_stats(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ошибка получения статистики" in call_args[0][0]


class TestSendMessageToUser:
    """Тесты для send_message_to_user command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "admin_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        context = Mock()
        context.args = ["987654321", "Test message"]
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_update, mock_context):
        """Тест successful send message command."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.log_message") as mock_log_message:
                mock_get_username.return_value = "target_user"

                await send_message_to_user(mock_update, mock_context)

                # Verify message was sent to user
                mock_context.bot.send_message.assert_called_once()
                bot_call_args = mock_context.bot.send_message.call_args
                assert bot_call_args[1]["chat_id"] == 987654321
                assert "Сообщение от администратора" in bot_call_args[1]["text"]

                # Verify confirmation to admin
                mock_update.message.reply_text.assert_called_once()
                admin_call_args = mock_update.message.reply_text.call_args
                assert "Сообщение отправлено" in admin_call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_message_no_args(self, mock_update, mock_context):
        """Тест send message command with no arguments."""
        mock_context.args = []

        await send_message_to_user(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Отправка сообщения пользователю" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_send_message_invalid_user_id(self, mock_update, mock_context):
        """Тест send message command with invalid user ID."""
        mock_context.args = ["invalid_id", "Test message"]

        await send_message_to_user(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Ошибка в ID пользователя" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_message_chat_not_found(self, mock_update, mock_context):
        """Тест send message command with chat not found error."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.log_message") as mock_log_message:
                mock_get_username.return_value = "target_user"
                mock_context.bot.send_message.side_effect = Exception("chat not found")

                await send_message_to_user(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Пользователь не найден" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_message_user_blocked(self, mock_update, mock_context):
        """Тест send message command with user blocked error."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.log_message") as mock_log_message:
                mock_get_username.return_value = "target_user"
                mock_context.bot.send_message.side_effect = Exception("blocked by user")

                await send_message_to_user(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Пользователь заблокировал бота" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_message_not_admin(self, mock_update, mock_context):
        """Тест send message command for non-admin user."""
        mock_update.effective_user.id = 987654321

        await send_message_to_user(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "нет прав администратора" in call_args[0][0]


class TestActivateUserCommand:
    """Тесты для activate_user_command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "admin_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        context = Mock()
        context.args = ["987654321"]
        return context

    @pytest.mark.asyncio
    async def test_activate_user_success(self, mock_update, mock_context):
        """Тест successful activate user command."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                with patch("bot_tg.admin_commands.activate_user") as mock_activate:
                    with patch("bot_tg.admin_commands.log_message") as mock_log_message:
                        mock_get_username.return_value = "target_user"
                        mock_is_active.return_value = False
                        mock_activate.return_value = True

                        await activate_user_command(mock_update, mock_context)

                        mock_update.message.reply_text.assert_called_once()
                        call_args = mock_update.message.reply_text.call_args
                        assert "Пользователь активирован" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_activate_user_already_active(self, mock_update, mock_context):
        """Тест activate user command when user is already active."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                mock_get_username.return_value = "target_user"
                mock_is_active.return_value = True

                await activate_user_command(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Пользователь уже активен" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_activate_user_no_args(self, mock_update, mock_context):
        """Тест activate user command with no arguments."""
        mock_context.args = []

        await activate_user_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Активация пользователя" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_activate_user_invalid_id(self, mock_update, mock_context):
        """Тест activate user command with invalid user ID."""
        mock_context.args = ["invalid_id"]

        await activate_user_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Ошибка в ID пользователя" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_activate_user_failure(self, mock_update, mock_context):
        """Тест activate user command with activation failure."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                with patch("bot_tg.admin_commands.activate_user") as mock_activate:
                    mock_get_username.return_value = "target_user"
                    mock_is_active.return_value = False
                    mock_activate.return_value = False

                    await activate_user_command(mock_update, mock_context)

                    mock_update.message.reply_text.assert_called_once()
                    call_args = mock_update.message.reply_text.call_args
                    assert "Ошибка активации пользователя" in call_args[0][0]


class TestDeactivateUserCommand:
    """Тесты для deactivate_user_command."""

    @pytest.fixture
    def mock_update(self):
        """Создать мок объект update."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "admin_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Создать мок объект context."""
        context = Mock()
        context.args = ["987654321"]
        return context

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, mock_update, mock_context):
        """Тест successful deactivate user command."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                with patch("bot_tg.admin_commands.deactivate_user") as mock_deactivate:
                    with patch("bot_tg.admin_commands.log_message") as mock_log_message:
                        mock_get_username.return_value = "target_user"
                        mock_is_active.return_value = True
                        mock_deactivate.return_value = True

                        await deactivate_user_command(mock_update, mock_context)

                        mock_update.message.reply_text.assert_called_once()
                        call_args = mock_update.message.reply_text.call_args
                        assert "Пользователь деактивирован" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_deactivate_user_already_inactive(self, mock_update, mock_context):
        """Тест deactivate user command when user is already inactive."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                mock_get_username.return_value = "target_user"
                mock_is_active.return_value = False

                await deactivate_user_command(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Пользователь уже неактивен" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_deactivate_admin(self, mock_update, mock_context):
        """Тест deactivate user command when trying to deactivate admin."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_admin") as mock_is_admin:
                mock_get_username.return_value = "admin_user"
                mock_is_admin.return_value = True

                await deactivate_user_command(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Нельзя деактивировать администратора" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_deactivate_user_no_args(self, mock_update, mock_context):
        """Тест deactivate user command with no arguments."""
        mock_context.args = []

        await deactivate_user_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Деактивация пользователя" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_deactivate_user_invalid_id(self, mock_update, mock_context):
        """Тест deactivate user command with invalid user ID."""
        mock_context.args = ["invalid_id"]

        await deactivate_user_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Ошибка в ID пользователя" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_deactivate_user_failure(self, mock_update, mock_context):
        """Тест deactivate user command with deactivation failure."""
        with patch("bot_tg.admin_commands.get_username_by_id") as mock_get_username:
            with patch("bot_tg.admin_commands.is_user_active") as mock_is_active:
                with patch("bot_tg.admin_commands.deactivate_user") as mock_deactivate:
                    mock_get_username.return_value = "target_user"
                    mock_is_active.return_value = True
                    mock_deactivate.return_value = False

                    await deactivate_user_command(mock_update, mock_context)

                    mock_update.message.reply_text.assert_called_once()
                    call_args = mock_update.message.reply_text.call_args
                    assert "Ошибка деактивации пользователя" in call_args[0][0]


class TestAdminCommandsIntegration:
    """Integration tests for admin commands."""

    @pytest.mark.asyncio
    async def test_full_admin_workflow(self):
        """Тест complete admin workflow."""
        # Создаем мок объекты для Update и Context
        mock_update = Mock()
        mock_update.effective_user.id = 123456789  # admin ID
        mock_update.message.reply_text = AsyncMock()

        mock_context = Mock()

        # Мокируем функции, которые требуют сложные зависимости
        mock_admin_menu = Mock()
        mock_logs = [Mock(), Mock()]
        mock_users = [Mock(), Mock()]

        with patch("bot_tg.telegram_bot.create_admin_menu", return_value=mock_admin_menu):
            with patch("db.utils.get_recent_logs", return_value=mock_logs):
                with patch("db.utils.get_users_list", return_value=mock_users):
                    # Тестируем последовательность админ команд
                    await admin_start(mock_update, mock_context)
                    await admin_logs(mock_update, mock_context)
                    await admin_users(mock_update, mock_context)

                    # Проверяем, что все функции были вызваны правильно
                    assert mock_update.message.reply_text.call_count == 3

                    # Проверяем содержимое первого вызова (admin_start)
                    call_args = mock_update.message.reply_text.call_args_list[0]
                    assert "Административная панель" in call_args[0][0]

    def test_format_datetime_edge_cases(self):
        """Тест format_datetime with various edge cases."""
        # Тест с разными форматами datetime
        assert format_datetime("2025-09-28T15:30:45.123Z") == "28.09.25 15:30:45"
        assert format_datetime("2025-09-28T15:30:45+03:00") == "28.09.25 15:30:45"

        # Тест с невалидными входами
        assert format_datetime(123) == 123
        assert format_datetime([]) == "N/A"  # Empty list is treated as falsy
        assert format_datetime({}) == "N/A"  # Empty dict is treated as falsy

    def test_is_admin_edge_cases(self):
        """Тест is_admin with edge cases."""
        # Тест с разными ID админов
        assert is_admin(123456789) is True
        assert is_admin(0) is False
        assert is_admin(-1) is False
        assert is_admin(999999999) is False
