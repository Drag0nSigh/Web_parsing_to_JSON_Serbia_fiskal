"""
Tests for user commands in bot_tg/user_commands.py
"""
import pytest
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Mock environment variables before importing user commands
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    with patch.dict(os.environ, {
        'TG_TOKEN': '123456789:TEST_TOKEN',
        'ADMIN_ID': '123456789',
        'DAILY_REQUEST_LIMIT': '50'
    }):
        yield

# Import user commands module with proper error handling
try:
    from bot_tg.user_commands import (
        start, help_command, admin_message, handle_message, is_url
    )
except ImportError as e:
    pytest.skip(f"User commands module not available: {e}", allow_module_level=True)


class TestIsUrl:
    """Tests for is_url function."""
    
    def test_is_url_valid_https(self):
        """Test valid HTTPS URL."""
        assert is_url("https://example.com") is True
        assert is_url("https://suf.purs.gov.rs/v/?vl=test") is True
        assert is_url("https://subdomain.example.com/path") is True
    
    def test_is_url_valid_http(self):
        """Test valid HTTP URL."""
        assert is_url("http://example.com") is True
        assert is_url("http://localhost:8080") is True
    
    def test_is_url_with_port(self):
        """Test URL with port."""
        assert is_url("https://example.com:8080") is True
        assert is_url("http://localhost:3000") is True
    
    def test_is_url_with_path(self):
        """Test URL with path and query parameters."""
        assert is_url("https://example.com/path?param=value") is True
        assert is_url("https://suf.purs.gov.rs/v/?vl=AzdWVDYyRUM0N1ZUNjJFQzQYWwEASVUBAHDBGAEAAAAAAAABmOyyJXMAAAAdrdjynx8FFJ7vKJSEWHehCSexnfVJwleCdnX8WapD%2FVqiutLId1kOu75ZXt4Z%2Bsp4oPEXjlYGf0jXnO6%2FcXPw%2FPXq9hZr9uVlrxjhiEVvc44J3xYEaqN2AGIwBxT%2Bco7LOqgAfE6PBUeQlA49tC%2FCvCkGuiVwfXwQfXAHyhDIs3Q29%2FfrLFsGoTpXECXvyKW%2FAg%2BxTXUFlO1zSxraDy2PbDNA%2FYSEYknv0LxtxUxuMU6FUL0fOXGM%2BmXcfYzRkDkjomzsdpiFGzuN9nRThzv16Q4S%2B9aznut5Fb2LWB85BaH4y11GtXMwubfQNzsdUpJZObMDZXcRx4V8tefqUmGlai%2FgEeT6FSrjHMGEP62UgDtokyrzuCqNeMz6JkZuHxE%2FqkLxZnYGwGUx5nRpiGEME1UyLQNUcWFsQgkJiyvWL3FpZsuRjXahZiNM5glVo1bbeISMK8%2BO8BsTPSHAg0jZkGpvi9OOT4qY8T0Zf1OMG4BnVTNM28h5ZMqobV8pjydfj%2BJtvsaDuNdv5C4Nhj3IC%2BaLeQdLFoL%2FfkA2%2F50HWUCi8KWMLVQHwYbJftNfYjPhjlrmbgG3FuDTWPM%2Bakut5GIUu4D8d1wmpqgQBenYX2qnqmcWhfNQu%2FBHz1KhizKvh2NLz%2FjWWiPicWVVM8H2cdU%2BGy4qdKkdk0WKiEtK362QBJnPpz%2BiUEFBoR6osNg%3D") is True
    
    def test_is_url_invalid(self):
        """Test invalid URLs."""
        assert is_url("not a url") is False
        assert is_url("ftp://example.com") is False
        assert is_url("example.com") is False
        assert is_url("") is False
        assert is_url("just text") is False
        assert is_url("https://") is False
    
    def test_is_url_edge_cases(self):
        """Test edge cases."""
        assert is_url("https://localhost") is True
        assert is_url("http://192.168.1.1") is True
        assert is_url("https://192.168.1.1:8080") is True
        assert is_url("https://example.com/") is True
        assert is_url("https://example.com?param=value") is True


class TestStart:
    """Tests for start command."""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_start_active_user(self, mock_update, mock_context):
        """Test start command for active user."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.is_admin', return_value=False):
                await start(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Добро пожаловать в бот" in call_args[0][0]
                assert call_args[1]['parse_mode'] == 'HTML'
    
    @pytest.mark.asyncio
    async def test_start_admin_user(self, mock_update, mock_context):
        """Test start command for admin user."""
        mock_update.effective_user.id = 123456789  # Admin ID
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.is_admin', return_value=True):
                with patch('bot_tg.telegram_bot.create_admin_menu') as mock_create_menu:
                    mock_create_menu.return_value = Mock()
                    
                    await start(mock_update, mock_context)
                    
                    mock_update.message.reply_text.assert_called_once()
                    call_args = mock_update.message.reply_text.call_args
                    assert "Добро пожаловать в бот" in call_args[0][0]
                    assert call_args[1]['parse_mode'] == 'HTML'
                    assert 'reply_markup' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_start_blocked_user_with_message_sent(self, mock_update, mock_context):
        """Test start command for blocked user who already sent message."""
        with patch('bot_tg.user_commands.is_user_active', return_value=False):
            with patch('bot_tg.user_commands.has_sent_blocked_message', return_value=True):
                await start(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Ваш аккаунт заблокирован" in call_args[0][0]
                assert "уже отправили сообщение" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_start_blocked_user_without_message_sent(self, mock_update, mock_context):
        """Test start command for blocked user who hasn't sent message."""
        with patch('bot_tg.user_commands.is_user_active', return_value=False):
            with patch('bot_tg.user_commands.has_sent_blocked_message', return_value=False):
                await start(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Ваш аккаунт заблокирован" in call_args[0][0]
                assert "одно сообщение" in call_args[0][0]
                assert "/admin" in call_args[0][0]


class TestHelpCommand:
    """Tests for help_command."""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_help_command_success(self, mock_update, mock_context):
        """Test successful help command."""
        await help_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Помощь по использованию бота" in call_args[0][0]
        assert call_args[1]['parse_mode'] == 'HTML'
        assert "/start" in call_args[0][0]
        assert "/help" in call_args[0][0]
        assert "/admin" in call_args[0][0]


class TestAdminMessage:
    """Tests for admin_message command."""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object."""
        context = Mock()
        context.args = ["Test message"]
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_admin_message_active_user_success(self, mock_update, mock_context):
        """Test admin message for active user with success."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.log_message') as mock_log_message:
                    mock_check_limit.return_value = {'can_make_request': True}
                    
                    await admin_message(mock_update, mock_context)
                    
                    # Verify message was sent to admin
                    mock_context.bot.send_message.assert_called_once()
                    bot_call_args = mock_context.bot.send_message.call_args
                    assert bot_call_args[1]['chat_id'] == 123456789
                    assert "Сообщение от пользователя" in bot_call_args[1]['text']
                    
                    # Verify confirmation to user
                    mock_update.message.reply_text.assert_called_once()
                    user_call_args = mock_update.message.reply_text.call_args
                    assert "Сообщение отправлено администратору" in user_call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_message_blocked_user_success(self, mock_update, mock_context):
        """Test admin message for blocked user with success."""
        with patch('bot_tg.user_commands.is_user_active', return_value=False):
            with patch('bot_tg.user_commands.has_sent_blocked_message', return_value=False):
                with patch('bot_tg.user_commands.log_message') as mock_log_message:
                    await admin_message(mock_update, mock_context)
                    
                    # Verify message was sent to admin
                    mock_context.bot.send_message.assert_called_once()
                    bot_call_args = mock_context.bot.send_message.call_args
                    assert "Заблокирован" in bot_call_args[1]['text']
                    
                    # Verify confirmation to user
                    mock_update.message.reply_text.assert_called_once()
                    user_call_args = mock_update.message.reply_text.call_args
                    assert "единственное сообщение" in user_call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_message_blocked_user_already_sent(self, mock_update, mock_context):
        """Test admin message for blocked user who already sent message."""
        with patch('bot_tg.user_commands.is_user_active', return_value=False):
            with patch('bot_tg.user_commands.has_sent_blocked_message', return_value=True):
                await admin_message(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Сообщение уже отправлено" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_message_daily_limit_exceeded(self, mock_update, mock_context):
        """Test admin message when daily limit is exceeded."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                mock_check_limit.return_value = {
                    'can_make_request': False,
                    'current_count': 50,
                    'limit': 50
                }
                
                await admin_message(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Дневной лимит исчерпан" in call_args[0][0]
                assert "50/50" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_message_no_args(self, mock_update, mock_context):
        """Test admin message with no arguments."""
        mock_context.args = []
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                mock_check_limit.return_value = {'can_make_request': True}
                
                await admin_message(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Отправка сообщения администратору" in call_args[0][0]
                assert "/admin" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_message_exception(self, mock_update, mock_context):
        """Test admin message with exception during sending."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.log_message') as mock_log_message:
                    mock_check_limit.return_value = {'can_make_request': True}
                    mock_context.bot.send_message.side_effect = Exception("Network error")
                    
                    await admin_message(mock_update, mock_context)
                    
                    # Should be called once for error message
                    assert mock_update.message.reply_text.call_count == 1
                    call_args = mock_update.message.reply_text.call_args
                    assert "Ошибка отправки сообщения" in call_args[0][0]


class TestHandleMessage:
    """Tests for handle_message function."""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.text = "https://example.com"
        update.message.reply_text = AsyncMock()
        update.message.reply_document = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_handle_message_blocked_user(self, mock_update, mock_context):
        """Test handle message for blocked user."""
        with patch('bot_tg.user_commands.is_user_active', return_value=False):
            await handle_message(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ваш аккаунт заблокирован" in call_args[0][0]
            assert "/admin" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_message_not_url(self, mock_update, mock_context):
        """Test handle message with non-URL text."""
        mock_update.message.text = "not a url"
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            await handle_message(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "не является ссылкой" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_message_daily_limit_exceeded(self, mock_update, mock_context):
        """Test handle message when daily limit is exceeded."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                mock_check_limit.return_value = {
                    'can_make_request': False,
                    'current_count': 50,
                    'limit': 50
                }
                
                await handle_message(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert "Дневной лимит исчерпан" in call_args[0][0]
                assert "50/50" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_message_success_with_list_result(self, mock_update, mock_context):
        """Test handle message with successful parsing returning list."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.parse_serbian_fiscal_url') as mock_parse:
                    with patch('bot_tg.user_commands.log_user_request') as mock_log_request:
                        mock_check_limit.return_value = {
                            'can_make_request': True,
                            'current_count': 1,
                            'limit': 50,
                            'remaining': 49
                        }
                        mock_parse.return_value = [{"test": "data"}]
                        
                        # Mock the processing message
                        mock_processing_msg = Mock()
                        mock_processing_msg.edit_text = AsyncMock()
                        mock_update.message.reply_text.return_value = mock_processing_msg
                        
                        await handle_message(mock_update, mock_context)
                        
                        # Verify processing message was sent
                        mock_update.message.reply_text.assert_called_once()
                        processing_call = mock_update.message.reply_text.call_args
                        assert "Обрабатываю ссылку" in processing_call[0][0]
                        
                        # Verify document was sent
                        mock_update.message.reply_document.assert_called_once()
                        doc_call = mock_update.message.reply_document.call_args
                        assert "fiscal_data_" in doc_call[1]['filename']
                        assert "JSON данные" in doc_call[1]['caption']
    
    @pytest.mark.asyncio
    async def test_handle_message_success_with_dict_result(self, mock_update, mock_context):
        """Test handle message with successful parsing returning dict."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.parse_serbian_fiscal_url') as mock_parse:
                    with patch('bot_tg.user_commands.log_user_request') as mock_log_request:
                        mock_check_limit.return_value = {
                            'can_make_request': True,
                            'current_count': 1,
                            'limit': 50,
                            'remaining': 49
                        }
                        mock_parse.return_value = {"test": "data"}
                        
                        # Mock the processing message
                        mock_processing_msg = Mock()
                        mock_processing_msg.edit_text = AsyncMock()
                        mock_update.message.reply_text.return_value = mock_processing_msg
                        
                        await handle_message(mock_update, mock_context)
                        
                        # Verify document was sent
                        mock_update.message.reply_document.assert_called_once()
                        doc_call = mock_update.message.reply_document.call_args
                        assert "fiscal_data_" in doc_call[1]['filename']
    
    @pytest.mark.asyncio
    async def test_handle_message_parsing_error(self, mock_update, mock_context):
        """Test handle message with parsing error."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.parse_serbian_fiscal_url') as mock_parse:
                    with patch('bot_tg.user_commands.log_user_request') as mock_log_request:
                        mock_check_limit.return_value = {'can_make_request': True}
                        mock_parse.side_effect = Exception("Parsing failed")
                        
                        # Mock the processing message
                        mock_processing_msg = Mock()
                        mock_processing_msg.edit_text = AsyncMock()
                        mock_update.message.reply_text.return_value = mock_processing_msg
                        
                        await handle_message(mock_update, mock_context)
                        
                        # Verify error message was sent
                        mock_processing_msg.edit_text.assert_called_once()
                        error_call = mock_processing_msg.edit_text.call_args
                        assert "Ошибка при обработке ссылки" in error_call[0][0]
                        assert "Parsing failed" in error_call[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_message_with_remaining_requests(self, mock_update, mock_context):
        """Test handle message with remaining requests info."""
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                with patch('bot_tg.user_commands.parse_serbian_fiscal_url') as mock_parse:
                    with patch('bot_tg.user_commands.log_user_request') as mock_log_request:
                        mock_check_limit.return_value = {
                            'can_make_request': True,
                            'current_count': 5,
                            'limit': 50,
                            'remaining': 45
                        }
                        mock_parse.return_value = [{"test": "data"}]
                        
                        # Mock the processing message
                        mock_processing_msg = Mock()
                        mock_processing_msg.edit_text = AsyncMock()
                        mock_update.message.reply_text.return_value = mock_processing_msg
                        
                        await handle_message(mock_update, mock_context)
                        
                        # Verify document was sent with correct info
                        mock_update.message.reply_document.assert_called_once()
                        doc_call = mock_update.message.reply_document.call_args
                        assert "5/50" in doc_call[1]['caption']


class TestUserCommandsIntegration:
    """Integration tests for user commands."""
    
    @pytest.mark.asyncio
    async def test_full_user_workflow(self):
        """Test complete user workflow."""
        # Test start command
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        
        context = Mock()
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.is_admin', return_value=False):
                await start(update, context)
                
                update.message.reply_text.assert_called_once()
                call_args = update.message.reply_text.call_args
                assert "Добро пожаловать в бот" in call_args[0][0]
    
    def test_is_url_comprehensive(self):
        """Test is_url function comprehensively."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com",
            "https://example.com:8080",
            "https://example.com/path",
            "https://example.com/path?param=value",
            "https://localhost",
            "http://192.168.1.1",
            "https://192.168.1.1:8080",
            "https://suf.purs.gov.rs/v/?vl=test",
            "https://example.com/",
            "https://example.com?param=value",
        ]
        
        for url in valid_urls:
            assert is_url(url), f"URL should be valid: {url}"
        
        # Invalid URLs
        invalid_urls = [
            "not a url",
            "ftp://example.com",
            "example.com",
            "",
            "just text",
            "https://",
            "file://example.com",
            "mailto:test@example.com",
        ]
        
        for url in invalid_urls:
            assert not is_url(url), f"URL should be invalid: {url}"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_admin_message(self):
        """Test error handling in admin_message."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        
        context = Mock()
        context.args = ["Test message"]
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        context.bot.send_message.side_effect = Exception("Bot error")
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.check_daily_limit') as mock_check_limit:
                mock_check_limit.return_value = {'can_make_request': True}
                
                await admin_message(update, context)
                
                # Should handle error gracefully
                assert update.message.reply_text.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_environment_variable_usage(self):
        """Test that environment variables are used correctly."""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 987654321
        update.effective_user.username = "test_user"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        
        context = Mock()
        
        with patch('bot_tg.user_commands.is_user_active', return_value=True):
            with patch('bot_tg.user_commands.is_admin', return_value=False):
                await start(update, context)
                
                call_args = update.message.reply_text.call_args
                # Check that environment variable is used in the message
                assert "50" in call_args[0][0]  # DAILY_REQUEST_LIMIT
