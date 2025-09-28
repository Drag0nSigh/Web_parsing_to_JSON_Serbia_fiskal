"""
Tests for telegram bot in bot_tg/telegram_bot.py
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Mock environment variables before importing bot modules
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    with patch.dict(os.environ, {
        'TG_TOKEN': '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'ADMIN_ID': '123456789',
        'DAILY_REQUEST_LIMIT': '50'
    }):
        yield

# Import telegram bot module with proper error handling
try:
    # Mock the environment before importing
    with patch.dict(os.environ, {
        'TG_TOKEN': '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'ADMIN_ID': '123456789',
        'DAILY_REQUEST_LIMIT': '50'
    }):
        from bot_tg.telegram_bot import (
            create_main_menu, create_admin_menu, button_callback, 
            error_handler, main, TG_TOKEN
        )
except ImportError as e:
    pytest.skip(f"Telegram bot module not available: {e}", allow_module_level=True)


class TestTelegramBotMenu:
    """Tests for menu creation functions."""
    
    def test_create_main_menu(self):
        """Test creation of main menu."""
        menu = create_main_menu()
        assert menu is not None
        assert hasattr(menu, 'inline_keyboard')
        assert len(menu.inline_keyboard) == 0  # Empty menu for regular users
    
    def test_create_admin_menu(self):
        """Test creation of admin menu."""
        menu = create_admin_menu()
        assert menu is not None
        assert hasattr(menu, 'inline_keyboard')
        assert len(menu.inline_keyboard) == 4  # 4 rows of buttons
        
        # Check that all expected buttons are present
        all_buttons = []
        for row in menu.inline_keyboard:
            for button in row:
                all_buttons.append(button.callback_data)
        
        expected_buttons = [
            "admin_logs", "admin_users", "admin_stats", "admin_test",
            "admin_send_message", "admin_status", "admin_activate", "admin_deactivate"
        ]
        
        for expected_button in expected_buttons:
            assert expected_button in all_buttons


class TestTelegramBotCallbacks:
    """Tests for button callback handling."""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object."""
        update = Mock()
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.id = "test_callback_id"
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "test_user"
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object."""
        context = Mock()
        context.processing_callbacks = set()
        return context
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_logs_success(self, mock_update, mock_context):
        """Test admin logs callback with successful data retrieval."""
        mock_update.callback_query.data = "admin_logs"
        
        # Mock admin check
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            # Mock database function
            with patch('db.utils.get_recent_logs') as mock_get_logs:
                mock_get_logs.return_value = [
                    {
                        'created_at': '2025-09-28 10:00:00',
                        'user_id': 123456789,
                        'username': 'test_user',
                        'status': 'success'
                    }
                ]
                
                await button_callback(mock_update, mock_context)
                
                # Verify callback was answered
                mock_update.callback_query.answer.assert_called_once()
                
                # Verify message was edited
                mock_update.callback_query.edit_message_text.assert_called_once()
                call_args = mock_update.callback_query.edit_message_text.call_args
                assert "📝" in call_args[0][0]  # Check for logs emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_logs_no_data(self, mock_update, mock_context):
        """Test admin logs callback with no data."""
        mock_update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_recent_logs') as mock_get_logs:
                mock_get_logs.return_value = []
                
                await button_callback(mock_update, mock_context)
                
                mock_update.callback_query.edit_message_text.assert_called_once()
                call_args = mock_update.callback_query.edit_message_text.call_args
                assert "Логи не найдены" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_logs_not_admin(self, mock_update, mock_context):
        """Test admin logs callback for non-admin user."""
        mock_update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=False):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "нет прав администратора" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_users_success(self, mock_update, mock_context):
        """Test admin users callback with successful data retrieval."""
        mock_update.callback_query.data = "admin_users"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_users_list') as mock_get_users:
                mock_get_users.return_value = [
                    {
                        'telegram_id': 123456789,
                        'username': 'test_user',
                        'is_active': True
                    }
                ]
                
                await button_callback(mock_update, mock_context)
                
                mock_update.callback_query.edit_message_text.assert_called_once()
                call_args = mock_update.callback_query.edit_message_text.call_args
                assert "👥" in call_args[0][0]  # Check for users emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_stats_success(self, mock_update, mock_context):
        """Test admin stats callback with successful data retrieval."""
        mock_update.callback_query.data = "admin_stats"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_system_stats') as mock_get_stats:
                with patch('db.utils.get_database_info') as mock_get_db_info:
                    mock_get_stats.return_value = {
                        'total_requests': 100,
                        'successful_requests': 95,
                        'failed_requests': 5,
                        'unique_users': 10
                    }
                    mock_get_db_info.return_value = {
                        'users_count': 10,
                        'logs_count': 100,
                        'connection_status': 'connected'
                    }
                    
                    await button_callback(mock_update, mock_context)
                    
                    mock_update.callback_query.edit_message_text.assert_called_once()
                    call_args = mock_update.callback_query.edit_message_text.call_args
                    assert "📊" in call_args[0][0]  # Check for stats emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_test_success(self, mock_update, mock_context):
        """Test admin test callback with successful parser test."""
        mock_update.callback_query.data = "admin_test"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('parser.fiscal_parser.parse_serbian_fiscal_url') as mock_parse:
                mock_parse.return_value = {"test": "data"}
                
                await button_callback(mock_update, mock_context)
                
                # Should be called twice: once for loading message, once for result
                assert mock_update.callback_query.edit_message_text.call_count == 2
                
                # Check final message contains success indicators
                final_call = mock_update.callback_query.edit_message_text.call_args_list[-1]
                assert "✅" in final_call[0][0]  # Success emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_test_parser_error(self, mock_update, mock_context):
        """Test admin test callback with parser error."""
        mock_update.callback_query.data = "admin_test"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('parser.fiscal_parser.parse_serbian_fiscal_url') as mock_parse:
                mock_parse.side_effect = Exception("Parser error")
                
                await button_callback(mock_update, mock_context)
                
                # Should be called twice: once for loading message, once for result
                assert mock_update.callback_query.edit_message_text.call_count == 2
                
                # Check final message contains error indicators
                final_call = mock_update.callback_query.edit_message_text.call_args_list[-1]
                assert "❌" in final_call[0][0]  # Error emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_send_message(self, mock_update, mock_context):
        """Test admin send message callback."""
        mock_update.callback_query.data = "admin_send_message"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "📨" in call_args[0][0]  # Check for send message emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_status_success(self, mock_update, mock_context):
        """Test admin status callback with successful system info."""
        mock_update.callback_query.data = "admin_status"
        
        # Мокируем psutil и platform модули для admin_status
        mock_psutil = Mock()
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = Mock(percent=60, used=8*1024**3, total=16*1024**3)
        mock_psutil.disk_usage.return_value = Mock(percent=45, used=200*1024**3, total=500*1024**3)
        
        mock_platform = Mock()
        mock_platform.system.return_value = "Windows"
        mock_platform.release.return_value = "10"
        
        mock_log_manager = Mock()
        mock_log_manager.get_log_stats.return_value = {
            'total_files': 15,
            'total_size': 2560,
            'retention_days': 30
        }
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch.dict('sys.modules', {'psutil': mock_psutil, 'platform': mock_platform}):
                with patch('utils.log_manager.get_log_manager', return_value=mock_log_manager):
                    with patch('bot_tg.admin_commands.datetime') as mock_datetime:
                        mock_datetime.now.return_value.strftime.return_value = "28.09.25 15:00:00"
                        
                        await button_callback(mock_update, mock_context)
                        
                        mock_update.callback_query.edit_message_text.assert_called_once()
                        call_args = mock_update.callback_query.edit_message_text.call_args
                        assert "🖥️" in call_args[0][0]  # Check for system emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_activate(self, mock_update, mock_context):
        """Test admin activate callback."""
        mock_update.callback_query.data = "admin_activate"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "✅" in call_args[0][0]  # Check for activate emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_deactivate(self, mock_update, mock_context):
        """Test admin deactivate callback."""
        mock_update.callback_query.data = "admin_deactivate"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "🚫" in call_args[0][0]  # Check for deactivate emoji
    
    @pytest.mark.asyncio
    async def test_button_callback_unknown_data(self, mock_update, mock_context):
        """Test button callback with unknown data."""
        mock_update.callback_query.data = "unknown_callback"
        
        await button_callback(mock_update, mock_context)
        
        # Should only answer the callback, not edit message
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_button_callback_processing_callbacks_tracking(self, mock_update, mock_context):
        """Test that processing callbacks are properly tracked."""
        mock_update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_recent_logs') as mock_get_logs:
                mock_get_logs.return_value = []
                
                await button_callback(mock_update, mock_context)
                
                # Check that callback ID was added and removed from processing set
                assert mock_update.callback_query.id not in mock_context.processing_callbacks


class TestTelegramBotErrorHandler:
    """Tests for error handler."""
    
    @pytest.mark.asyncio
    async def test_error_handler_message_not_modified(self):
        """Test error handler ignores 'Message is not modified' error."""
        update = Mock()
        context = Mock()
        context.error = Exception("Message is not modified")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Should log info about ignoring the error
            mock_logger.info.assert_called_once()
            assert "Message is not modified" in mock_logger.info.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_error_handler_general_error(self):
        """Test error handler for general errors."""
        update = Mock()
        update.effective_message = Mock()
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        context.error = Exception("General error")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Should log the error
            mock_logger.error.assert_called_once()
            
            # Should reply to user
            update.effective_message.reply_text.assert_called_once()
            call_args = update.effective_message.reply_text.call_args[0][0]
            assert "Произошла внутренняя ошибка" in call_args
    
    @pytest.mark.asyncio
    async def test_error_handler_no_effective_message(self):
        """Test error handler when there's no effective message."""
        update = Mock()
        update.effective_message = None
        context = Mock()
        context.error = Exception("General error")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Should log the error
            mock_logger.error.assert_called_once()
            
            # Should not try to reply since there's no effective message
            # (This is the current behavior, but could be improved)


class TestTelegramBotMain:
    """Tests for main function."""
    
    def test_tg_token_validation(self):
        """Test that TG_TOKEN is properly validated."""
        # This test verifies the token validation logic in the module
        assert TG_TOKEN is not None
        assert ':' in TG_TOKEN  # Token should be in format "BOT_ID:TOKEN"
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.Application')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_success(self, mock_logger, mock_app_class, mock_init_db):
        """Test successful main function execution."""
        # Mock application
        mock_app = Mock()
        mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
        
        # Mock init_database to not raise exception
        mock_init_db.return_value = None
        
        # This would normally run the bot, but we'll just test the setup
        try:
            main()
        except SystemExit:
            # Expected when run_polling is called
            pass
        
        # Verify database was initialized
        mock_init_db.assert_called_once()
        
        # Verify application was created
        mock_app_class.builder.assert_called_once()
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_database_error(self, mock_logger, mock_init_db):
        """Test main function with database initialization error."""
        # Mock init_database to raise exception
        mock_init_db.side_effect = Exception("Database error")
        
        # Should return early on database error
        result = main()
        assert result is None
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Ошибка инициализации БД" in mock_logger.error.call_args[0][0]
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.Application')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_application_error(self, mock_logger, mock_app_class, mock_init_db):
        """Test main function with application creation error."""
        # Mock init_database to succeed
        mock_init_db.return_value = None
        
        # Mock Application to raise exception
        mock_app_class.builder.return_value.token.return_value.build.side_effect = Exception("App error")
        
        # Should raise the exception
        with pytest.raises(Exception, match="App error"):
            main()
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Ошибка создания приложения Telegram" in mock_logger.error.call_args[0][0]


class TestTelegramBotIntegration:
    """Integration tests for telegram bot."""
    
    @pytest.mark.asyncio
    async def test_full_callback_flow(self):
        """Test complete callback flow from start to finish."""
        # Create mock objects
        update = Mock()
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.id = "test_callback_id"
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "test_user"
        
        context = Mock()
        context.processing_callbacks = set()
        
        # Test admin logs callback
        update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_recent_logs') as mock_get_logs:
                mock_get_logs.return_value = [
                    {
                        'created_at': '2025-09-28 10:00:00',
                        'user_id': 123456789,
                        'username': 'test_user',
                        'status': 'success'
                    }
                ]
                
                await button_callback(update, context)
                
                # Verify all expected calls were made
                update.callback_query.answer.assert_called_once()
                update.callback_query.edit_message_text.assert_called_once()
                
                # Verify callback was properly tracked
                assert update.callback_query.id not in context.processing_callbacks
    
    def test_menu_creation_consistency(self):
        """Test that menu creation functions return consistent types."""
        main_menu = create_main_menu()
        admin_menu = create_admin_menu()
        
        # Both should return InlineKeyboardMarkup objects
        assert hasattr(main_menu, 'inline_keyboard')
        assert hasattr(admin_menu, 'inline_keyboard')
        
        # Main menu should be empty
        assert len(main_menu.inline_keyboard) == 0
        
        # Admin menu should have buttons
        assert len(admin_menu.inline_keyboard) > 0
        
        # All buttons should have proper structure
        for row in admin_menu.inline_keyboard:
            for button in row:
                assert hasattr(button, 'text')
                assert hasattr(button, 'callback_data')
                assert button.text is not None
                assert button.callback_data is not None
