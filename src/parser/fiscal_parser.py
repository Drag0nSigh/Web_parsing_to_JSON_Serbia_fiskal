"""
Парсер для извлечения фискальных данных с динамических страниц
"""

import logging
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from models.fiscal_models import (
    AmountsNds,
    AmountsReceiptNds,
    Document,
    FiscalData,
    Item,
    Receipt,
    SerbianFiscalData,
    Ticket,
)
from utils.log_manager import get_log_manager

# Получаем менеджер логов
log_manager = get_log_manager()

# Настраиваем логирование
logger = log_manager.setup_logging("parser", logging.DEBUG)
# Принудительно устанавливаем уровень DEBUG
logger.setLevel(logging.DEBUG)


class FiscalParser:
    """Парсер для сербских фискальных данных"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._setup_driver()

    def _setup_driver(self):
        """Настройка Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        # Агрессивные оптимизации для максимальной скорости
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        # Дополнительные оптимизации запуска
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        # НЕ отключаем JavaScript - нужен для Knockout.js
        # chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-java")
        chrome_options.add_argument("--disable-flash")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-downloads")
        chrome_options.add_argument("--disable-preconnect")
        chrome_options.add_argument("--disable-dns-prefetch")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-domain-reliability")
        chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
        chrome_options.add_argument("--disable-features=MediaRouter")
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--memory-pressure-off")

        # Отключаем загрузку изображений и CSS для ускорения
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Отключаем логирование
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")

        # Размер окна
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Используем системный chromedriver в Docker
        import os

        if os.path.exists("/usr/bin/chromedriver"):
            service = Service("/usr/bin/chromedriver")
        else:
            # Fallback для локальной разработки
            service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Уменьшаем время ожидания
        self.driver.implicitly_wait(5)
        self.driver.set_page_load_timeout(30)

        return self.driver

    def parse_url(self, url: str) -> SerbianFiscalData:
        """Парсинг фискальных данных по URL"""
        # Проверяем, что драйвер работает
        try:
            if not self.driver or not self.driver.service.is_connectable():
                self._setup_driver()
        except:
            self._setup_driver()

        try:
            logger.info(f"🌐 Загружаем страницу: {url}")
            # Загружаем страницу
            self.driver.get(url)

            logger.info("⏳ Ждем загрузки данных...")
            # Ждем загрузки Knockout.js и данных
            self._wait_for_data_loading()

            logger.info("📄 Получаем HTML...")
            # Получаем HTML после выполнения JavaScript
            html_content = self.driver.page_source

            logger.info("🔍 Парсим данные...")
            # Парсим данные
            return self._parse_html_content(html_content)

        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге: {e}")
            import traceback

            traceback.print_exc()
            # Если парсинг не удался, возвращаем пустые данные
            return SerbianFiscalData(
                tin="",
                shop_name="",
                shop_address="",
                city="",
                administrative_unit="",
                invoice_number="",
                total_amount=Decimal("0"),
                transaction_type_counter=0,
                total_counter=0,
                invoice_counter_extension="",
                signed_by="",
                sdc_date_time=datetime.now(),
                buyer_id=None,
                requested_by="",
                invoice_type="",
                transaction_type="",
                status="",
                items=[],
            )

    def _wait_for_data_loading(self):
        """Ожидание загрузки данных через Knockout.js"""
        try:
            # Ждем исчезновения спиннера загрузки
            start_time = time.time()
            WebDriverWait(self.driver, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".sk-spinner")))
            logger.info(f"✅ Спиннер загрузки исчез за {time.time() - start_time} секунд")

            # Открываем список товаров (спецификацию)
            logger.info("🔍 Ищем кнопку для открытия списка товаров...")
            try:
                # Ищем кнопку "Спецификација рачуна"
                specs_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#collapse-specs']"))
                )
                logger.info("✅ Найдена кнопка спецификации")

                # Проверяем, открыт ли уже список
                collapse_div = self.driver.find_element(By.CSS_SELECTOR, "#collapse-specs")
                if "show" not in collapse_div.get_attribute("class"):
                    logger.info("📂 Открываем список товаров...")
                    specs_button.click()
                    time.sleep(0.25)  # Ждем анимации открытия
                    logger.info("✅ Список товаров открыт")
                else:
                    logger.info("✅ Список товаров уже открыт")

            except Exception as e:
                logger.warning(f"⚠️ Не удалось открыть список товаров: {e}")

            # Ждем появления данных в таблице - пробуем разные селекторы
            selectors_to_try = [
                "tbody[data-bind*='Specifications'] tr",  # Knockout.js биндинг - ПРИОРИТЕТ
                "tbody[data-bind*='foreach: Specifications'] tr",  # Точный биндинг
                "table tbody[data-bind*='Specifications'] tr",  # Таблица с биндингом
                "table.invoice-table tbody tr",
                "table tbody tr",
                "tbody tr",
                ".invoice-table tbody tr",
                "table tr",
                "tr[data-bind*='Specifications']",
                "table.invoice-table tbody",
            ]

            table_found = False
            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"✅ Найдена таблица с селектором: {selector}")
                    table_found = True
                    break
                except:
                    logger.debug(f"❌ Не найдена таблица с селектором: {selector}")
                    continue

            if not table_found:
                logger.warning("⚠️ Таблица с товарами не найдена")

            # Дополнительная пауза для полной загрузки
            time.sleep(0.5)  # Уменьшаем время ожидания

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при ожидании загрузки: {e}")
            # Продолжаем выполнение даже если ожидание не удалось
            time.sleep(0.5)

    def _parse_html_content(self, html_content: str) -> SerbianFiscalData:
        """Парсинг HTML контента"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Извлекаем основные данные
        data = {
            "tin": self._extract_tin(soup),
            "shop_name": self._extract_shop_name(soup),
            "shop_address": self._extract_shop_address(soup),
            "city": self._extract_city(soup),
            "administrative_unit": self._extract_administrative_unit(soup),
            "invoice_number": self._extract_invoice_number(soup),
            "total_amount": self._extract_total_amount(soup),
            "transaction_type_counter": self._extract_transaction_type_counter(soup),
            "total_counter": self._extract_total_counter(soup),
            "invoice_counter_extension": self._extract_invoice_counter_extension(soup),
            "signed_by": self._extract_signed_by(soup),
            "sdc_date_time": self._extract_sdc_date_time(soup),
            "buyer_id": self._extract_buyer_id(soup),
            "requested_by": self._extract_requested_by(soup),
            "invoice_type": self._extract_invoice_type(soup),
            "transaction_type": self._extract_transaction_type(soup),
            "status": self._extract_status(soup),
            "items": self._extract_items_from_table(soup),
        }

        return SerbianFiscalData(**data)

    def _extract_tin(self, soup: BeautifulSoup) -> str:
        """Извлечение ПИБ"""
        tin_element = soup.find("span", {"id": "tinLabel"})
        return tin_element.get_text(strip=True) if tin_element else ""

    def _extract_shop_name(self, soup: BeautifulSoup) -> str:
        """Извлечение названия магазина"""
        shop_element = soup.find("span", {"id": "shopFullNameLabel"})
        return shop_element.get_text(strip=True) if shop_element else ""

    def _extract_shop_address(self, soup: BeautifulSoup) -> str:
        """Извлечение адреса магазина"""
        address_element = soup.find("span", {"id": "addressLabel"})
        return address_element.get_text(strip=True) if address_element else ""

    def _extract_city(self, soup: BeautifulSoup) -> str:
        """Извлечение города"""
        city_element = soup.find("span", {"id": "cityLabel"})
        return city_element.get_text(strip=True) if city_element else ""

    def _extract_administrative_unit(self, soup: BeautifulSoup) -> str:
        """Извлечение општины"""
        admin_element = soup.find("span", {"id": "administrativeUnitLabel"})
        return admin_element.get_text(strip=True) if admin_element else ""

    def _extract_invoice_number(self, soup: BeautifulSoup) -> str:
        """Извлечение номера чека"""
        invoice_element = soup.find("span", {"id": "invoiceNumberLabel"})
        return invoice_element.get_text(strip=True) if invoice_element else ""

    def _extract_total_amount(self, soup: BeautifulSoup) -> Decimal:
        """Извлечение общей суммы"""
        total_element = soup.find("span", {"id": "totalAmountLabel"})
        if total_element:
            amount_text = total_element.get_text(strip=True)
            # Используем улучшенный парсер
            return self._parse_serbian_number(amount_text)
        return Decimal("0")

    def _extract_transaction_type_counter(self, soup: BeautifulSoup) -> int:
        """Извлечение счетчика по типу транзакции"""
        counter_element = soup.find("span", {"id": "transactionTypeCounterLabel"})
        if counter_element:
            return int(counter_element.get_text(strip=True))
        return 0

    def _extract_total_counter(self, soup: BeautifulSoup) -> int:
        """Извлечение общего счетчика"""
        counter_element = soup.find("span", {"id": "totalCounterLabel"})
        if counter_element:
            return int(counter_element.get_text(strip=True))
        return 0

    def _extract_invoice_counter_extension(self, soup: BeautifulSoup) -> str:
        """Извлечение расширения счетчика чека"""
        extension_element = soup.find("span", {"id": "invoiceCounterExtensionLabel"})
        return extension_element.get_text(strip=True) if extension_element else ""

    def _extract_signed_by(self, soup: BeautifulSoup) -> str:
        """Извлечение подписи"""
        signed_element = soup.find("span", {"id": "signedByLabel"})
        return signed_element.get_text(strip=True) if signed_element else ""

    def _extract_sdc_date_time(self, soup: BeautifulSoup) -> datetime:
        """Извлечение времени ПФР"""
        date_element = soup.find("span", {"id": "sdcDateTimeLabel"})
        logger.info(f'sdcDateTimeLabel = {date_element}')
        if date_element:
            date_text = date_element.get_text(strip=True)
            logger.info(f'date_text = {date_text}')
            
            # Список форматов для попытки парсинга
            date_formats = [
                "%m/%d/%Y %I:%M:%S %p",  # Американский формат: 3/8/2026 1:08:19 PM
                "%d.%m.%Y. %H:%M:%S",     # Европейский формат: 08.03.2026. 13:08:19
                "%d.%m.%Y %H:%M:%S",      # Европейский формат без точки: 08.03.2026 13:08:19
                "%Y-%m-%d %H:%M:%S",      # ISO формат: 2026-03-08 13:08:19
            ]
            
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_text, date_format)
                    logger.info(f'ИТОГОВАЯ ДАТА = {parsed_date} (формат: {date_format})')
                    return parsed_date
                except ValueError:
                    continue
            
            logger.warning(f'Не удалось распарсить дату "{date_text}" ни одним из форматов')
        
        logger.info('Дата не обнаружена')
        return datetime.now()

    def _extract_buyer_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлечение ID покупателя"""
        buyer_element = soup.find("span", {"id": "buyerIdLabel"})
        buyer_text = buyer_element.get_text(strip=True) if buyer_element else ""
        return buyer_text if buyer_text else None

    def _extract_requested_by(self, soup: BeautifulSoup) -> str:
        """Извлечение информации о том, кто затребовал"""
        requested_element = soup.find("span", {"id": "requestedByLabel"})
        return requested_element.get_text(strip=True) if requested_element else ""

    def _extract_invoice_type(self, soup: BeautifulSoup) -> str:
        """Извлечение типа чека"""
        type_element = soup.find("span", {"id": "invoiceTypeId"})
        return type_element.get_text(strip=True) if type_element else ""

    def _extract_transaction_type(self, soup: BeautifulSoup) -> str:
        """Извлечение типа транзакции"""
        type_element = soup.find("span", {"id": "transactionTypeId"})
        return type_element.get_text(strip=True) if type_element else ""

    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Извлечение статуса чека"""
        status_element = soup.find("label", {"id": "invoiceStatusLabel"})
        return status_element.get_text(strip=True) if status_element else ""

    def _extract_items_from_table(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение товаров из таблицы после загрузки Knockout.js"""
        items = []

        logger.info("🔍 Поиск товаров в HTML...")

        # Сохраняем HTML для отладки
        debug_filename = f"debug_{datetime.now().strftime('%Y-%m-%d')}.html"
        debug_path = log_manager.get_writable_file_path(debug_filename)

        if debug_path:
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(str(soup.prettify()))
                logger.info(f"💾 HTML сохранен в {debug_path} для отладки")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить HTML для отладки: {e}")
        else:
            logger.warning("⚠️ Нет доступа для записи файла отладки")

        # Метод 1: Ищем по Knockout.js биндингам
        items = self._extract_items_by_knockout_binding(soup)
        if items:
            logger.info(f"✅ Найдено товаров через Knockout.js: {len(items)}")
            return items

        # Метод 2: Ищем все строки таблиц
        all_rows = soup.find_all("tr")
        logger.info(f"📊 Найдено строк таблиц: {len(all_rows)}")

        # Показываем первые несколько строк для отладки
        for i, row in enumerate(all_rows[:10]):
            cells = row.find_all(["td", "th"])
            if cells:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                logger.debug(f"  Строка {i}: {cell_texts}")

        for i, row in enumerate(all_rows):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 4:  # Минимум 4 колонки (название, количество, цена, сумма)
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                logger.debug(f"  🔍 Проверяем строку {i}: {cell_texts}")

                # Проверяем, похожа ли строка на товар
                if self._is_item_row(cell_texts):
                    logger.debug(f"  ✅ Строка {i} похожа на товар")
                    try:
                        item = self._parse_item_row(cells)
                        if item and item.get("name"):  # Только если есть название
                            items.append(item)
                            logger.info(
                                f"  ✅ Товар {len(items)}: {item['name']} - "
                                f"{item['quantity']} x {item['price']} = {item['sum']}"
                            )
                        elif item is None:
                            logger.debug(f"  ⚠️ Строка пропущена (заголовок таблицы)")
                        else:
                            logger.warning(f"  ❌ Товар не создан или без названия")
                    except Exception as e:
                        logger.error(f"  ❌ Ошибка парсинга строки: {e}")
                        continue
                else:
                    logger.debug(f"  ❌ Строка {i} не похожа на товар")

        # Метод 3: Если товары не найдены, ищем по тексту
        if not items:
            logger.info("🔍 Товары не найдены в таблицах, ищем по тексту...")
            items = self._extract_items_by_text_search(soup)

        logger.info(f"📦 Итого найдено товаров: {len(items)}")
        return items

    def _extract_items_by_knockout_binding(self, soup: BeautifulSoup) -> List[Dict]:
        """Поиск товаров через Knockout.js биндинги"""
        logger.info("🔧 ТЕСТ: DEBUG сообщение работает!")
        items = []

        # Ищем только элементы с data-bind="foreach: Specifications" (не все с Specifications)
        knockout_elements = soup.find_all(attrs={"data-bind": lambda x: x and "foreach: Specifications" in x})
        logger.info(f"🔗 Найдено Knockout.js элементов: {len(knockout_elements)}")

        # Обрабатываем только первый tbody элемент, чтобы избежать дублирования
        if knockout_elements:
            knockout_elements = [knockout_elements[0]]
            logger.info(f"🔧 Обрабатываем только первый tbody элемент для избежания дублирования")

        for element in knockout_elements:
            logger.debug(f"  Knockout элемент: {element.name} - {element.get('data-bind')}")

            # Ищем строки внутри этого элемента
            rows = element.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 4:  # Минимум 4 колонки
                    try:
                        item = self._parse_item_row(cells)
                        if item and item.get("name"):
                            items.append(item)
                            logger.info(f"    ✅ Товар: {item['name']}")
                        elif item is None:
                            logger.debug(f"    ⚠️ Строка пропущена (заголовок таблицы)")
                    except Exception as e:
                        logger.error(f"    ❌ Ошибка: {e}")

        logger.info(f"✅ Найдено товаров через Knockout.js: {len(items)}")
        return items

    def _extract_items_by_text_search(self, soup: BeautifulSoup) -> List[Dict]:
        """Поиск товаров по тексту (fallback метод)"""
        items = []

        logger.info("🔍 Поиск товаров по тексту...")

        # Ищем все элементы с текстом, содержащим числа и цены
        text_content = soup.get_text()

        # Ищем строки, которые могут быть товарами
        lines = text_content.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(char.isdigit() for char in line):
                # Проверяем, содержит ли строка паттерны товара
                if self._looks_like_item_line(line):
                    logger.debug(f"  📝 Возможный товар: {line[:100]}...")
                    # Пытаемся извлечь данные из строки
                    item = self._extract_item_from_line(line)
                    if item:
                        items.append(item)
                        logger.info(f"  ✅ Добавлен товар: {item['name']}")

        return items

    def _extract_item_from_line(self, line: str) -> Optional[Dict]:
        """Извлечение товара из строки текста"""
        import re

        # Ищем числа в сербском формате
        numbers = re.findall(r"\d+[.,]\d+", line)
        if len(numbers) >= 3:  # Минимум количество, цена, сумма
            try:
                # Пытаемся извлечь название товара (до первого числа)
                name_match = re.match(r"^([^0-9]+)", line)
                name = name_match.group(1).strip() if name_match else "Товар"

                # Парсим числа
                quantity = self._parse_serbian_number(numbers[0])
                price = self._parse_serbian_number(numbers[1])
                total = self._parse_serbian_number(numbers[2])

                # Определяем НДС по умолчанию
                nds_type = 2  # 10%

                return {
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "sum": total,
                    "nds_type": nds_type,
                    "tax_base": total * Decimal("0.909"),  # Примерный расчет
                    "vat_amount": total * Decimal("0.091"),
                    "label": "Е",
                }
            except Exception as e:
                logger.error(f"  ❌ Ошибка извлечения товара: {e}")
                return None

        return None

    def _looks_like_item_line(self, line: str) -> bool:
        """Проверяет, похожа ли строка на товар"""
        # Ищем паттерны: название + количество + цена + сумма
        import re

        # Проверяем наличие чисел в сербском формате
        serbian_numbers = re.findall(r"\d+[.,]\d+", line)
        if len(serbian_numbers) >= 2:  # Минимум количество и цена
            return True

        return False

    def _is_item_row(self, cell_texts: List[str]) -> bool:
        """Проверяет, является ли строка товаром"""
        if len(cell_texts) < 4:  # Минимум название, количество, цена, сумма
            return False

        # Проверяем, не является ли строка заголовком таблицы
        header_keywords = ["назив", "количина", "јед. цена", "укупна цена", "основица", "пдв", "стопа"]
        first_cell = cell_texts[0].strip().lower()

        # Если первая ячейка содержит только заголовочные слова, это заголовок
        if first_cell in header_keywords:
            return False

        # Проверяем, что все ячейки не являются заголовочными словами
        all_header_cells = all(cell.strip().lower() in header_keywords for cell in cell_texts if cell.strip())
        if all_header_cells:
            return False

        # Проверяем наличие числовых значений в колонках
        try:
            # Колонка 1 (количество) должна быть числом
            quantity = cell_texts[1].replace(",", ".")
            float(quantity)

            # Колонка 2 (цена) должна быть числом
            price = cell_texts[2].replace(".", "").replace(",", ".")
            float(price)

            # Колонка 3 (сумма) должна быть числом
            total = cell_texts[3].replace(".", "").replace(",", ".")
            float(total)

            # Проверяем, что название не пустое
            if not cell_texts[0].strip():
                return False

            return True
        except:
            return False

    def _parse_item_row(self, cells) -> Dict:
        """Парсит строку товара"""
        name = cells[0].get_text(strip=True)
        quantity_text = cells[1].get_text(strip=True)
        unit_price_text = cells[2].get_text(strip=True)
        total_text = cells[3].get_text(strip=True)
        tax_base_text = cells[4].get_text(strip=True) if len(cells) > 4 else "0"
        vat_amount_text = cells[5].get_text(strip=True) if len(cells) > 5 else "0"
        label = cells[6].get_text(strip=True) if len(cells) > 6 else "Е"

        # Дополнительная проверка на заголовок таблицы
        header_keywords = ["назив", "количина", "јед. цена", "укупна цена", "основица", "пдв", "стопа"]
        if name.lower() in header_keywords:
            logger.debug(f"    ⚠️ Пропускаем заголовок таблицы: {name}")
            return None

        logger.debug(f"    📝 Парсим товар: {name} | {quantity_text} | {unit_price_text} | {total_text}")

        # Парсим числовые значения
        quantity = self._parse_serbian_number(quantity_text) if quantity_text else Decimal("0")
        unit_price = self._parse_serbian_number(unit_price_text)
        total = self._parse_serbian_number(total_text)

        # Определяем тип НДС по лейблу
        nds_type = 2  # По умолчанию 10%
        if "Ђ" in label or "20" in label:
            nds_type = 3  # 20%
        elif "Е" in label or "10" in label:
            nds_type = 2  # 10%
        elif "А" in label:
            nds_type = 1  # Без НДС

        return {
            "name": name,
            "quantity": quantity,
            "price": unit_price,
            "sum": total,
            "nds_type": nds_type,
            "tax_base": self._parse_serbian_number(tax_base_text),
            "vat_amount": self._parse_serbian_number(vat_amount_text),
            "label": label,
        }

    def _parse_serbian_number(self, text: str) -> Decimal:
        """Парсинг сербских и смешанных чисел.
        Сербский: 1.359,98 (точка — тысячи, запятая — десятичная).
        С точкой как десятичной: 93.99, 1.00 — точку не убирать.
        US: 1,359.98 (запятая — тысячи, точка — десятичная).
        """
        if not text:
            return Decimal("0")

        import re

        text = text.strip()
        text = re.sub(r"\s+", "", text)

        has_dot = "." in text
        has_comma = "," in text

        if has_comma and has_dot:
            # Оба разделителя: последний — десятичный
            last_dot = text.rfind(".")
            last_comma = text.rfind(",")
            if last_comma > last_dot:
                # Сербский: 1.359,98
                # Проверка: в сербском формате должна быть только одна запятая (десятичный разделитель)
                if text.count(",") > 1:
                    logger.warning(f"⚠️ Невалидный сербский формат (множественные запятые): '{text}'")
                    return Decimal("0")
                cleaned_text = text.replace(".", "").replace(",", ".")
            else:
                # US: 1,359.98
                # Проверка: в US формате должна быть только одна точка (десятичный разделитель)
                # и запятые только для разделения тысяч
                if text.count(",") > 1 or text.count(".") > 1:
                    logger.warning(f"⚠️ Невалидный US формат (множественные разделители): '{text}'")
                    return Decimal("0")
                cleaned_text = text.replace(",", "")
        elif has_dot and not has_comma:
            # Только точка — десятичный разделитель (93.99, 1.00)
            cleaned_text = text
        else:
            # Только запятая (93,99) или без разделителя
            cleaned_text = text.replace(",", ".")

        cleaned_text = re.sub(r"[^\d\.\-]", "", cleaned_text)

        if not cleaned_text or cleaned_text in ["-", "."]:
            return Decimal("0")

        # Проверка на валидность формата: должна быть максимум одна точка (десятичный разделитель)
        if cleaned_text.count(".") > 1:
            logger.warning(f"⚠️ Невалидный формат числа (множественные точки): '{text}' -> '{cleaned_text}'")
            return Decimal("0")

        try:
            return Decimal(cleaned_text)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось распарсить число '{text}' -> '{cleaned_text}': {e}")
            return Decimal("0")

    def _extract_knockout_data(self, soup: BeautifulSoup) -> Dict:
        """Извлечение данных Knockout.js"""
        data = {}
        knockout_elements = soup.find_all(attrs={"data-bind": True})
        for element in knockout_elements:
            binding = element.get("data-bind", "")
            if "text:" in binding:
                field_name = binding.split("text:")[1].strip()
                data[field_name] = element.get_text(strip=True)
        return data

    def _extract_knockout_items(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение товаров через Knockout.js"""
        items = []
        # Ищем элементы с data-bind для товаров
        item_elements = soup.find_all(attrs={"data-bind": lambda x: x and "foreach" in x})

        for element in item_elements:
            # Ищем дочерние элементы с данными товаров
            child_elements = element.find_all(attrs={"data-bind": True})

            # Группируем элементы по товарам
            current_item = None
            for child in child_elements:
                binding = child.get("data-bind", "")
                text = child.get_text(strip=True)

                if "text: name" in binding:
                    # Если это новый товар, сохраняем предыдущий
                    if current_item:
                        items.append(current_item)

                    # Создаем новый товар
                    current_item = {
                        "name": text,
                        "quantity": Decimal("1"),
                        "price": Decimal("0"),
                        "sum": Decimal("0"),
                        "nds_type": 2,
                        "payment_type": 1,
                        "product_type": 1,
                    }
                elif current_item:
                    if "text: quantity" in binding:
                        try:
                            current_item["quantity"] = Decimal(text)
                        except (ValueError, InvalidOperation):
                            current_item["quantity"] = Decimal("1")
                    elif "text: unitPrice" in binding:
                        current_item["price"] = self._parse_serbian_number(text)
                    elif "text: amount" in binding:
                        current_item["sum"] = self._parse_serbian_number(text)

            # Добавляем последний товар
            if current_item:
                items.append(current_item)

        return items

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты в сербском формате"""
        if not date_str or not date_str.strip():
            return None

        try:
            # Сербский формат: DD.MM.YYYY. HH:MM:SS
            return datetime.strptime(date_str.strip(), "%d.%m.%Y. %H:%M:%S")
        except ValueError:
            try:
                # Альтернативный формат без точки в конце
                return datetime.strptime(date_str.strip(), "%d.%m.%Y %H:%M:%S")
            except ValueError:
                return None

    def _extract_city_from_address(self, address: str) -> str:
        """Извлечение города из адреса"""
        if not address or not address.strip():
            return "Unknown"

        # Ищем последнюю часть после запятой
        parts = address.split(",")
        if len(parts) > 1:
            city = parts[-1].strip()
            # Убираем скобки и дополнительные части
            city = city.split("(")[0].strip()
            return city if city else "Unknown"

        return "Unknown"

    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        if self.driver is None:
            self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SerbianToRussianConverter:
    """Конвертер сербских данных в российский формат"""

    def __init__(self, serbian_data: SerbianFiscalData):
        self.serbian_data = serbian_data

    def convert(self) -> FiscalData:
        """Конвертация сербских данных в российский формат"""
        import random

        # Генерируем случайный ID по образцу rus.json (24 символа)
        import string

        random_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        logger.info(f"🔧 Генерируем ID: {random_id}")
        logger.info(f"🔧 Дата создания: {self.serbian_data.sdc_date_time}")


        # Создаем товары на основе извлеченных данных
        items = []
        for item_data in self.serbian_data.items:
            # Количество как Decimal; цена и сумма — в копейки (динры * 100).
            # Если уже пришли целые (копейки) — не умножаем на 100 повторно.
            quantity = Decimal(str(item_data["quantity"]))
            raw_price = item_data["price"]
            raw_sum = item_data["sum"]
            if isinstance(raw_price, int) and isinstance(raw_sum, int):
                price = raw_price
                sum_val = raw_sum
            else:
                price = int(float(raw_price) * 100)
                sum_val = int(float(raw_sum) * 100)

            item = Item(
                name=item_data["name"],
                quantity=quantity,
                price=price,
                sum=sum_val,
                nds=item_data["nds_type"],
                paymentType=4,  # По умолчанию наличные
                productType=1,  # Товар
            )
            items.append(item)

        # Если товары не найдены, создаем один общий товар
        if not items:
            total_cents = int(float(self.serbian_data.total_amount) * 100)
            item = Item(
                name="Товары/услуги",
                quantity=Decimal("1"),  # 1 товар
                price=total_cents,
                sum=total_cents,
                nds=2,  # НДС 10%
                paymentType=1,
                productType=1,
            )
            items.append(item)

        # Конвертируем общую сумму в копейки
        total_cents = int(float(self.serbian_data.total_amount) * 100)

        # Рассчитываем НДС по товарам
        nds_amounts = {}
        for item in items:
            nds_type = item.nds
            if nds_type not in nds_amounts:
                nds_amounts[nds_type] = 0

            # Рассчитываем НДС (примерно 10% от суммы товара)
            if nds_type == 2:  # НДС 10%
                nds_amount = int(item.sum * 0.1)  # 10% НДС
            elif nds_type == 3:  # НДС 20%
                nds_amount = int(item.sum * 0.2)  # 20% НДС
            else:
                nds_amount = 0

            nds_amounts[nds_type] += nds_amount

        # Создаем amountsReceiptNds
        amounts_nds_list = []
        for nds_type, nds_sum in nds_amounts.items():
            if nds_sum > 0:
                amounts_nds_list.append(AmountsNds(nds=nds_type, ndsSum=nds_sum))

        amounts_receipt_nds = AmountsReceiptNds(amountsNds=amounts_nds_list) if amounts_nds_list else None

        # Создаем чек
        receipt = Receipt(
            code=3,  # Код документа
            dateTime=self.serbian_data.sdc_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
            fiscalDocumentNumber=self.serbian_data.total_counter,
            fiscalDriveNumber="0000000000000000",  # Заглушка
            fiscalSign=int(self.serbian_data.transaction_type_counter),
            fnsUrl="www.nalog.gov.rs",  # Сербский аналог
            kktRegId=self.serbian_data.tin,
            totalSum=total_cents,
            ecashTotalSum=total_cents,  # Предполагаем безналичную оплату
            operationType=1,  # Продажа
            taxationType=2,  # УСН доходы
            appliedTaxationType=2,
            user=self.serbian_data.shop_name,
            userInn=self.serbian_data.tin,
            retailPlace=self.serbian_data.shop_name,
            retailPlaceAddress=f"{self.serbian_data.shop_address}, {self.serbian_data.city}",
            items=items,
            amountsReceiptNds=amounts_receipt_nds,
        )

        # Создаем документ
        document = Document(receipt=receipt)
        ticket = Ticket(document=document)

        # Создаем фискальные данные с правильными полями
        logger.info(f"🔧 Создаем FiscalData с ID: {random_id}")
        logger.info(f"🔧 Создаем FiscalData с created_at: {self.serbian_data.sdc_date_time}")

        fiscal_data = FiscalData(ticket=ticket)

        logger.debug(f"🔧 FiscalData создан без ID и created_at:")
        logger.debug(f"   ID: {fiscal_data.id}")
        logger.debug(f"   Created: {fiscal_data.created_at}")

        # Устанавливаем значения после создания
        fiscal_data.id = random_id
        fiscal_data.created_at = self.serbian_data.sdc_date_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        logger.debug(f"🔧 FiscalData после установки значений:")
        logger.debug(f"   ID: {fiscal_data.id}")
        logger.debug(f"   Created: {fiscal_data.created_at}")
        logger.info(f"   FiscalData: {fiscal_data}")

        return fiscal_data


def convert_to_russian_format(serbian_data):
    """Конвертация в российский формат"""

    # Создаем товары для российского формата
    items = []
    for item_data in serbian_data.items:
        item = Item(
            name=item_data["name"],
            quantity=item_data["quantity"],
            price=item_data["price"],
            sum=item_data["sum"],
            nds=item_data["nds_type"],
            payment_type="card",  # По умолчанию карта
            product_type=1,  # Товар
        )
        items.append(item)

    # Создаем чек
    receipt = Receipt(
        code=3,  # Код документа
        date_time=serbian_data.sdc_date_time,
        fiscal_document_number=serbian_data.total_counter,
        fiscal_drive_number="0000000000000000",  # Заглушка
        fiscal_sign=int(serbian_data.transaction_type_counter),
        fns_url="www.nalog.gov.rs",  # Сербский аналог
        kkt_reg_id=serbian_data.tin,
        total_sum=serbian_data.total_amount,
        ecash_total_sum=serbian_data.total_amount,  # Предполагаем безналичную оплату
        operation_type=1,  # Продажа
        taxation_type=2,  # УСН доходы
        applied_taxation_type=2,
        user=serbian_data.shop_name,
        user_inn=serbian_data.tin,
        retail_place=serbian_data.shop_name,
        retail_place_address=f"{serbian_data.shop_address}, {serbian_data.city}",
        items=items,
    )

    # Создаем документ
    document = Document(receipt=receipt)
    ticket = Ticket(document=document)

    return FiscalData(ticket=ticket)


def parse_serbian_fiscal_url(url: str, headless: bool = True) -> Dict:
    """Основная функция для парсинга сербских фискальных данных по URL"""

    # Создаем новый парсер при каждом вызове
    with FiscalParser(headless=headless) as parser:
        # Парсим данные с сайта
        serbian_data = parser.parse_url(url)

        # Конвертируем в российский формат
        logger.info(f"🔧 Конвертируем данные...")
        logger.info(f"   TIN: {serbian_data.tin}")
        logger.info(f"   Shop: {serbian_data.shop_name}")
        logger.info(f"   Total: {serbian_data.total_amount}")
        logger.info(f"   Items: {len(serbian_data.items)}")

        converter = SerbianToRussianConverter(serbian_data)
        russian_data = converter.convert()

        logger.info(f"✅ Конвертация завершена")
        logger.info(f"   ID: {russian_data.id}")
        logger.info(f"   Created: {russian_data.created_at}")

        # Возвращаем массив как в rus.json
        return [russian_data.model_dump(mode="json", by_alias=True)]
