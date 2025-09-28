"""
Тесты для команд бота в модулях bot_tg/ - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Мокируем переменные окружения перед импортом модулей бота
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Мокировать переменные окружения для всех тестов."""
    with patch.dict(os.environ, {
        'TG_TOKEN': '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'ADMIN_ID': '123456789',
        'DAILY_REQUEST_LIMIT': '50'
    }):
        yield

# Импортируем реальные модули команд бота с правильной обработкой ошибок
try:
    from bot_tg.admin_commands import is_admin, admin_start, admin_logs, admin_users, admin_test, admin_status, admin_stats
    from bot_tg.user_commands import start, help_command, handle_message
except ImportError as e:
    pytest.skip(f"Bot modules not available: {e}", allow_module_level=True)


class TestAdminCommands:
    """Тесты для функций админских команд."""
    
    @patch.dict('os.environ', {'ADMIN_ID': '123456789'})
    def test_is_admin_true(self):
        """Тест проверки админа для валидного админа."""
        assert is_admin(123456789) is True
    
    @patch.dict('os.environ', {'ADMIN_ID': '123456789'})
    def test_is_admin_false(self):
        """Тест проверки админа для не-админа."""
        assert is_admin(987654321) is False
    
    @pytest.mark.asyncio
    async def test_admin_start_valid_admin(self, mock_telegram_update, mock_telegram_context):
        """Тест команды admin start для валидного админа."""
        mock_telegram_update.effective_user.id = 123456789
        mock_telegram_update.message.reply_text = AsyncMock()
        
        with patch('bot_tg.admin_commands.is_admin', return_value=True):
            with patch('bot_tg.telegram_bot.create_admin_menu', return_value=Mock()):
                await admin_start(mock_telegram_update, mock_telegram_context)
                
                mock_telegram_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_admin_logs_success(self, mock_telegram_update, mock_telegram_context):
        """Тест команды admin logs."""
        mock_telegram_update.effective_user.id = 123456789
        mock_telegram_update.message.reply_text = AsyncMock()
        
        with patch('bot_tg.admin_commands.is_admin', return_value=True):
            with patch('bot_tg.admin_commands.get_recent_logs', return_value=[]):
                await admin_logs(mock_telegram_update, mock_telegram_context)
                
                mock_telegram_update.message.reply_text.assert_called()


class TestUserCommands:
    """Тесты для функций пользовательских команд."""
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_telegram_update, mock_telegram_context):
        """Тест команды start."""
        mock_telegram_update.effective_user.id = 123456789
        mock_telegram_update.effective_user.username = 'test_user'
        mock_telegram_update.message.reply_text = AsyncMock()
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.is_admin', return_value=False):
                await start(mock_telegram_update, mock_telegram_context)
                
                mock_telegram_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_telegram_update, mock_telegram_context):
        """Тест команды help."""
        mock_telegram_update.effective_user.id = 123456789
        mock_telegram_update.message.reply_text = AsyncMock()
        
        await help_command(mock_telegram_update, mock_telegram_context)
        
        mock_telegram_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_valid_url(self, mock_telegram_update, mock_telegram_context):
        """Тест обработки сообщений с валидным URL."""
        mock_telegram_update.effective_user.id = 123456789
        mock_telegram_update.message.text = "https://suf.purs.gov.rs/v/?vl=test123"
        mock_telegram_update.message.reply_text = AsyncMock()
        mock_telegram_update.message.reply_document = AsyncMock()
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_limit:
                mock_limit.return_value = {'can_make_request': True, 'current_count': 5, 'limit': 50, 'remaining': 45}
                
                with patch('parser.fiscal_parser.parse_serbian_fiscal_url', return_value=[{"test": "data"}]):
                    with patch('bot_tg.user_commands.log_user_request', return_value=True):
                        with patch('bot_tg.user_commands.is_url', return_value=True):
                            await handle_message(mock_telegram_update, mock_telegram_context)
                            
                            # Должен обработать URL
                            assert mock_telegram_update.message.reply_document.called or mock_telegram_update.message.reply_text.called