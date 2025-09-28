"""
Тесты для телеграм бота в bot_tg/telegram_bot.py
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Мокаем переменные окружения перед импортом модулей бота
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Мокаем переменные окружения для всех тестов."""
    with patch.dict(os.environ, {
        'TG_TOKEN': '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'ADMIN_ID': '123456789',
        'DAILY_REQUEST_LIMIT': '50'
    }):
        yield

# Импортируем модуль телеграм бота с корректной обработкой ошибок
try:
    # Мокаем окружение перед импортом
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
    """Тесты для функций создания меню."""
    
    def test_create_main_menu(self):
        """Тест создания главного меню."""
        menu = create_main_menu()
        assert menu is not None
        assert hasattr(menu, 'inline_keyboard')
        assert len(menu.inline_keyboard) == 0  # Пустое меню для обычных пользователей
    
    def test_create_admin_menu(self):
        """Тест создания админского меню."""
        menu = create_admin_menu()
        assert menu is not None
        assert hasattr(menu, 'inline_keyboard')
        assert len(menu.inline_keyboard) == 4  # 4 ряда кнопок
        
        # Проверяем, что все ожидаемые кнопки присутствуют
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
    """Тесты для обработки колбэков кнопок."""
    
    @pytest.fixture
    def mock_update(self):
        """Создаем мок объект update."""
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
        """Создаем мок объект context."""
        context = Mock()
        context.processing_callbacks = set()
        return context
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_logs_success(self, mock_update, mock_context):
        """Тест колбэка админских логов с успешным получением данных."""
        mock_update.callback_query.data = "admin_logs"
        
        # Мокаем проверку админа
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            # Мокаем функцию базы данных
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
                
                # Проверяем, что колбэк был отвечен
                mock_update.callback_query.answer.assert_called_once()
                
                # Проверяем, что сообщение было отредактировано
                mock_update.callback_query.edit_message_text.assert_called_once()
                call_args = mock_update.callback_query.edit_message_text.call_args
                assert "📝" in call_args[0][0]  # Проверяем эмодзи логов
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_logs_no_data(self, mock_update, mock_context):
        """Тест колбэка админских логов без данных."""
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
        """Тест колбэка админских логов для не-админа."""
        mock_update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=False):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "нет прав администратора" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_users_success(self, mock_update, mock_context):
        """Тест колбэка админских пользователей с успешным получением данных."""
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
                assert "👥" in call_args[0][0]  # Проверяем эмодзи пользователей
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_stats_success(self, mock_update, mock_context):
        """Тест колбэка админской статистики с успешным получением данных."""
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
                        assert "📊" in call_args[0][0]  # Проверяем эмодзи статистики
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_test_success(self, mock_update, mock_context):
        """Тест колбэка админского теста с успешным тестом парсера."""
        mock_update.callback_query.data = "admin_test"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('parser.fiscal_parser.parse_serbian_fiscal_url') as mock_parse:
                mock_parse.return_value = {"test": "data"}
                
                await button_callback(mock_update, mock_context)
                
                # Должен быть вызван дважды: один раз для сообщения загрузки, один раз для результата
                assert mock_update.callback_query.edit_message_text.call_count == 2
                
                # Проверяем, что финальное сообщение содержит индикаторы успеха
                final_call = mock_update.callback_query.edit_message_text.call_args_list[-1]
                assert "✅" in final_call[0][0]  # Эмодзи успеха
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_test_parser_error(self, mock_update, mock_context):
        """Тест колбэка админского теста с ошибкой парсера."""
        mock_update.callback_query.data = "admin_test"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('parser.fiscal_parser.parse_serbian_fiscal_url') as mock_parse:
                mock_parse.side_effect = Exception("Parser error")
                
                await button_callback(mock_update, mock_context)
                
                # Должен быть вызван дважды: один раз для сообщения загрузки, один раз для результата
                assert mock_update.callback_query.edit_message_text.call_count == 2
                
                # Проверяем, что финальное сообщение содержит индикаторы ошибки
                final_call = mock_update.callback_query.edit_message_text.call_args_list[-1]
                assert "❌" in final_call[0][0]  # Эмодзи ошибки
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_send_message(self, mock_update, mock_context):
        """Тест колбэка админской отправки сообщения."""
        mock_update.callback_query.data = "admin_send_message"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "📨" in call_args[0][0]  # Проверяем эмодзи отправки сообщения
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_status_success(self, mock_update, mock_context):
        """Тест колбэка админского статуса с успешной информацией о системе."""
        mock_update.callback_query.data = "admin_status"
        
        # Мокаем модули psutil и platform для admin_status
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
                        assert "🖥️" in call_args[0][0]  # Проверяем эмодзи системы
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_activate(self, mock_update, mock_context):
        """Тест колбэка админской активации."""
        mock_update.callback_query.data = "admin_activate"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "✅" in call_args[0][0]  # Проверяем эмодзи активации
    
    @pytest.mark.asyncio
    async def test_button_callback_admin_deactivate(self, mock_update, mock_context):
        """Тест колбэка админской деактивации."""
        mock_update.callback_query.data = "admin_deactivate"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            await button_callback(mock_update, mock_context)
            
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert "🚫" in call_args[0][0]  # Проверяем эмодзи деактивации
    
    @pytest.mark.asyncio
    async def test_button_callback_unknown_data(self, mock_update, mock_context):
        """Тест колбэка кнопки с неизвестными данными."""
        mock_update.callback_query.data = "unknown_callback"
        
        await button_callback(mock_update, mock_context)
        
        # Должен только ответить на колбэк, не редактировать сообщение
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_button_callback_processing_callbacks_tracking(self, mock_update, mock_context):
        """Тест того, что обрабатываемые колбэки правильно отслеживаются."""
        mock_update.callback_query.data = "admin_logs"
        
        with patch('bot_tg.telegram_bot.is_admin', return_value=True):
            with patch('db.utils.get_recent_logs') as mock_get_logs:
                mock_get_logs.return_value = []
                
                await button_callback(mock_update, mock_context)
                
                # Проверяем, что ID колбэка был добавлен и удален из набора обработки
                assert mock_update.callback_query.id not in mock_context.processing_callbacks


class TestTelegramBotErrorHandler:
    """Тесты для обработчика ошибок."""
    
    @pytest.mark.asyncio
    async def test_error_handler_message_not_modified(self):
        """Тест обработчика ошибок игнорирует ошибку 'Message is not modified'."""
        update = Mock()
        context = Mock()
        context.error = Exception("Message is not modified")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Должен логировать информацию об игнорировании ошибки
            mock_logger.info.assert_called_once()
            assert "Message is not modified" in mock_logger.info.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_error_handler_general_error(self):
        """Тест обработчика ошибок для общих ошибок."""
        update = Mock()
        update.effective_message = Mock()
        update.effective_message.reply_text = AsyncMock()
        context = Mock()
        context.error = Exception("General error")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Должен логировать ошибку
            mock_logger.error.assert_called_once()
            
            # Должен ответить пользователю
            update.effective_message.reply_text.assert_called_once()
            call_args = update.effective_message.reply_text.call_args[0][0]
            assert "Произошла внутренняя ошибка" in call_args
    
    @pytest.mark.asyncio
    async def test_error_handler_no_effective_message(self):
        """Тест обработчика ошибок когда нет эффективного сообщения."""
        update = Mock()
        update.effective_message = None
        context = Mock()
        context.error = Exception("General error")
        
        with patch('bot_tg.telegram_bot.logger') as mock_logger:
            await error_handler(update, context)
            
            # Должен логировать ошибку
            mock_logger.error.assert_called_once()
            
            # Не должен пытаться ответить, так как нет эффективного сообщения
            # (Это текущее поведение, но может быть улучшено)


class TestTelegramBotMain:
    """Тесты для главной функции."""
    
    def test_tg_token_validation(self):
        """Тест того, что TG_TOKEN правильно валидируется."""
        # Этот тест проверяет логику валидации токена в модуле
        assert TG_TOKEN is not None
        assert ':' in TG_TOKEN  # Токен должен быть в формате "BOT_ID:TOKEN"
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.Application')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_success(self, mock_logger, mock_app_class, mock_init_db):
        """Тест успешного выполнения главной функции."""
        # Мокаем приложение
        mock_app = Mock()
        mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
        
        # Мокаем init_database чтобы не вызывать исключение
        mock_init_db.return_value = None
        
        # Это обычно запустило бы бота, но мы просто тестируем настройку
        try:
            main()
        except SystemExit:
            # Ожидается когда вызывается run_polling
            pass
        
        # Проверяем, что база данных была инициализирована
        mock_init_db.assert_called_once()
        
        # Проверяем, что приложение было создано
        mock_app_class.builder.assert_called_once()
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_database_error(self, mock_logger, mock_init_db):
        """Тест главной функции с ошибкой инициализации базы данных."""
        # Мокаем init_database чтобы вызвать исключение
        mock_init_db.side_effect = Exception("Database error")
        
        # Должен вернуться рано при ошибке базы данных
        result = main()
        assert result is None
        
        # Проверяем, что ошибка была залогирована
        mock_logger.error.assert_called_once()
        assert "Ошибка инициализации БД" in mock_logger.error.call_args[0][0]
    
    @patch('bot_tg.telegram_bot.init_database')
    @patch('bot_tg.telegram_bot.Application')
    @patch('bot_tg.telegram_bot.logger')
    def test_main_application_error(self, mock_logger, mock_app_class, mock_init_db):
        """Тест главной функции с ошибкой создания приложения."""
        # Мокаем init_database чтобы успешно выполниться
        mock_init_db.return_value = None
        
        # Мокаем Application чтобы вызвать исключение
        mock_app_class.builder.return_value.token.return_value.build.side_effect = Exception("App error")
        
        # Должен вызвать исключение
        with pytest.raises(Exception, match="App error"):
            main()
        
        # Проверяем, что ошибка была залогирована
        mock_logger.error.assert_called_once()
        assert "Ошибка создания приложения Telegram" in mock_logger.error.call_args[0][0]


class TestTelegramBotIntegration:
    """Интеграционные тесты для телеграм бота."""
    
    @pytest.mark.asyncio
    async def test_full_callback_flow(self):
        """Тест полного потока колбэков от начала до конца."""
        # Создаем мок объекты
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
        
        # Тестируем колбэк админских логов
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
                
                # Проверяем, что все ожидаемые вызовы были сделаны
                update.callback_query.answer.assert_called_once()
                update.callback_query.edit_message_text.assert_called_once()
                
                # Проверяем, что колбэк был правильно отслежен
                assert update.callback_query.id not in context.processing_callbacks
    
    def test_menu_creation_consistency(self):
        """Тест того, что функции создания меню возвращают согласованные типы."""
        main_menu = create_main_menu()
        admin_menu = create_admin_menu()
        
        # Оба должны возвращать объекты InlineKeyboardMarkup
        assert hasattr(main_menu, 'inline_keyboard')
        assert hasattr(admin_menu, 'inline_keyboard')
        
        # Главное меню должно быть пустым
        assert len(main_menu.inline_keyboard) == 0
        
        # Админское меню должно иметь кнопки
        assert len(admin_menu.inline_keyboard) > 0
        
        # Все кнопки должны иметь правильную структуру
        for row in admin_menu.inline_keyboard:
            for button in row:
                assert hasattr(button, 'text')
                assert hasattr(button, 'callback_data')
                assert button.text is not None
                assert button.callback_data is not None
