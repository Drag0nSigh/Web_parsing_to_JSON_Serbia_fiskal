"""
Конфигурация pytest и фикстуры для проекта парсера фискальных данных.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, date
from decimal import Decimal

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Переменные окружения для тестов
os.environ.update({
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_PORT': '5433',
    'POSTGRES_DB': 'test_fiscal_data',
    'POSTGRES_USER': 'test_user',
    'POSTGRES_PASSWORD': 'test_password',
    'TG_TOKEN': 'test_token',
    'ADMIN_ID': '123456789',
    'LOG_RETENTION_DAYS': '7',
    'DAILY_REQUEST_LIMIT': '10'
})

@pytest.fixture
def temp_log_dir():
    """Создать временную директорию для логов для тестирования."""
    import logging
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        # Закрываем все обработчики логов перед удалением
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers[:]:
                try:
                    handler.close()
                    logger.removeHandler(handler)
                except:
                    pass
        
        # Также очищаем корневой логгер
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            try:
                handler.close()
                root_logger.removeHandler(handler)
            except:
                pass
        
        # Принудительно удаляем временную директорию
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

@pytest.fixture
def mock_log_manager(temp_log_dir):
    """Мок менеджера логов с временной директорией."""
    with patch('utils.log_manager.LogManager') as mock_class:
        mock_instance = Mock()
        mock_instance.log_dir = temp_log_dir
        mock_instance.log_retention_days = 7
        mock_instance.get_daily_log_file.return_value = temp_log_dir / "test_2025-09-27.log"
        mock_instance.can_write_to_log_dir.return_value = True
        mock_instance.get_writable_file_path.return_value = temp_log_dir / "test.log"
        mock_instance.get_log_stats.return_value = {
            'total_files': 3,
            'total_size': 1024,
            'retention_days': 7,
            'by_type': {'bot': 1, 'parser': 1, 'database': 1}
        }
        mock_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_database():
    """Мок сессии базы данных и операций."""
    with patch('db.database.get_session') as mock_session:
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        yield mock_db

@pytest.fixture
def sample_serbian_data():
    """Образец сербских фискальных данных для тестирования."""
    return {
        'tin': '123456789',
        'shop_name': 'Test Shop',
        'shop_address': 'Test Address 123',
        'city': 'Belgrade',
        'administrative_unit': 'Београд',
        'invoice_number': 'INV-001',
        'total_amount': Decimal('183.96'),
        'transaction_type_counter': 456,
        'total_counter': 123,
        'invoice_counter_extension': 'EXT-001',
        'signed_by': 'Test Signer',
        'sdc_date_time': datetime(2025, 9, 27, 10, 30, 0),
        'buyer_id': None,
        'requested_by': 'Test Requester',
        'invoice_type': 'NORMAL',
        'transaction_type': 'SALE',
        'status': 'VALID',
        'items': [
            {
                'name': 'Test Item',
                'quantity': Decimal('1'),
                'price': Decimal('183.96'),
                'sum': Decimal('183.96'),
                'nds_type': 2
            }
        ]
    }

@pytest.fixture
def sample_russian_data():
    """Образец российских фискальных данных для тестирования."""
    return {
        '_id': '66ce2f2a5b87f45c8a123456',
        'createdAt': '2025-09-27T10:30:00+00:00',
        'ticket': {
            'document': {
                'receipt': {
                    'cashTotalSum': 0,
                    'code': 3,
                    'creditSum': 0,
                    'dateTime': '2025-09-27T10:30:00',
                    'ecashTotalSum': 18396,
                    'fiscalDocumentFormatVer': 4,
                    'fiscalDocumentNumber': 123,
                    'fiscalDriveNumber': '0000000000000000',
                    'fiscalSign': 456,
                    'fnsUrl': 'www.nalog.gov.rs',
                    'items': [
                        {
                            'name': 'Test Item',
                            'quantity': 1,
                            'price': 18396,
                            'sum': 18396,
                            'nds': 2,
                            'paymentType': 4,
                            'productType': 1
                        }
                    ],
                    'kktRegId': '123456789',
                    'nds0': 0,
                    'amountsReceiptNds': {
                        'amountsNds': [
                            {
                                'nds': 2,
                                'ndsSum': 1759
                            }
                        ]
                    },
                    'operationType': 1,
                    'retailPlace': 'Test Shop',
                    'retailPlaceAddress': 'Test Address 123',
                    'taxationType': 2,
                    'appliedTaxationType': 2,
                    'totalSum': 18396,
                    'user': 'Test Shop',
                    'userInn': '123456789'
                }
            }
        }
    }

@pytest.fixture
def sample_url():
    """Образец сербского фискального URL для тестирования."""
    return "https://suf.purs.gov.rs/v/?vl=test123"

@pytest.fixture
def mock_selenium_driver():
    """Мок Selenium WebDriver."""
    with patch('selenium.webdriver.Chrome') as mock_driver_class:
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        
        # Мок исходного кода страницы
        mock_driver.page_source = """
        <html>
            <body>
                <div id="invoice-data">
                    <div class="tin">123456789</div>
                    <div class="shop-name">Test Shop</div>
                    <div class="address">Test Address 123, Belgrade</div>
                    <div class="total">183,96</div>
                    <div class="item">
                        <span class="name">Test Item</span>
                        <span class="quantity">1</span>
                        <span class="price">183,96</span>
                    </div>
                </div>
            </body>
        </html>
        """
        yield mock_driver

@pytest.fixture
def mock_telegram_update():
    """Мок объекта Telegram Update."""
    from unittest.mock import AsyncMock
    mock_update = Mock()
    mock_update.effective_user.id = 123456789
    mock_update.effective_user.username = 'test_user'
    mock_update.message.text = '/start'
    mock_update.message.reply_text = AsyncMock()
    mock_update.message.reply_document = AsyncMock()
    return mock_update

@pytest.fixture
def mock_telegram_context():
    """Мок объекта Telegram Context."""
    from unittest.mock import AsyncMock
    mock_context = Mock()
    mock_context.bot.send_message = AsyncMock()
    mock_context.bot.send_document = AsyncMock()
    return mock_context


# Вспомогательные функции для тестов команд бота
def is_admin(user_id: int) -> bool:
    """Вспомогательная функция для проверки администратора в тестах."""
    return user_id == 123456789


def create_admin_menu():
    """Вспомогательная функция для создания мока админского меню."""
    return Mock()


def create_main_menu():
    """Вспомогательная функция для создания мока главного меню."""
    return Mock()


# Отсутствующие функции из db.utils, которые ожидают тесты
def activate_user(user_id: int) -> bool:
    """Мок функции активации пользователя."""
    return True


def deactivate_user(user_id: int) -> bool:
    """Мок функции деактивации пользователя."""
    return True


def get_username_by_id(user_id: int) -> str:
    """Мок функции получения имени пользователя."""
    return f"user_{user_id}"
