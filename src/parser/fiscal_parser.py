"""
Парсер для извлечения фискальных данных с динамических страниц
"""
import time
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from models.fiscal_models import SerbianFiscalData, FiscalData, Receipt, Item, Document, Ticket, AmountsNds, AmountsReceiptNds


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
        
        # Кэшируем драйвер для повторного использования
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Уменьшаем время ожидания
        self.driver.implicitly_wait(5)
        self.driver.set_page_load_timeout(30)
    
    def parse_url(self, url: str) -> SerbianFiscalData:
        """Парсинг фискальных данных по URL"""
        # Проверяем, что драйвер работает
        try:
            if not self.driver or not self.driver.service.is_connectable():
                self._setup_driver()
        except:
            self._setup_driver()
        
        try:
            print(f"🌐 Загружаем страницу: {url}")
            # Загружаем страницу
            self.driver.get(url)
            
            print("⏳ Ждем загрузки данных...")
            # Ждем загрузки Knockout.js и данных
            self._wait_for_data_loading()
            
            print("📄 Получаем HTML...")
            # Получаем HTML после выполнения JavaScript
            html_content = self.driver.page_source
            
            print("🔍 Парсим данные...")
            # Парсим данные
            return self._parse_html_content(html_content)
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге: {e}")
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
                total_amount=Decimal('0'),
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
                items=[]
            )
    
    def _wait_for_data_loading(self):
        """Ожидание загрузки данных через Knockout.js"""
        try:
            # Ждем исчезновения спиннера загрузки
            start_time = time.time()
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".sk-spinner"))
            )
            print(f"✅ Спиннер загрузки исчез за {time.time() - start_time} секунд")
            
            # Открываем список товаров (спецификацию)
            print("🔍 Ищем кнопку для открытия списка товаров...")
            try:
                # Ищем кнопку "Спецификација рачуна"
                specs_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#collapse-specs']"))
                )
                print("✅ Найдена кнопка спецификации")
                
                # Проверяем, открыт ли уже список
                collapse_div = self.driver.find_element(By.CSS_SELECTOR, "#collapse-specs")
                if "show" not in collapse_div.get_attribute("class"):
                    print("📂 Открываем список товаров...")
                    specs_button.click()
                    time.sleep(0.25)  # Ждем анимации открытия
                    print("✅ Список товаров открыт")
                else:
                    print("✅ Список товаров уже открыт")
                    
            except Exception as e:
                print(f"⚠️ Не удалось открыть список товаров: {e}")
            
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
                "table.invoice-table tbody"
            ]
            
            table_found = False
            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Найдена таблица с селектором: {selector}")
                    table_found = True
                    break
                except:
                    print(f"❌ Не найдена таблица с селектором: {selector}")
                    continue
            
            if not table_found:
                print("⚠️ Таблица с товарами не найдена")
            
            # Дополнительная пауза для полной загрузки
            time.sleep(0.5)  # Уменьшаем время ожидания
            
        except Exception as e:
            print(f"⚠️ Ошибка при ожидании загрузки: {e}")
            # Продолжаем выполнение даже если ожидание не удалось
            time.sleep(0.5)
    
    def _parse_html_content(self, html_content: str) -> SerbianFiscalData:
        """Парсинг HTML контента"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Извлекаем основные данные
        data = {
            'tin': self._extract_tin(soup),
            'shop_name': self._extract_shop_name(soup),
            'shop_address': self._extract_shop_address(soup),
            'city': self._extract_city(soup),
            'administrative_unit': self._extract_administrative_unit(soup),
            'invoice_number': self._extract_invoice_number(soup),
            'total_amount': self._extract_total_amount(soup),
            'transaction_type_counter': self._extract_transaction_type_counter(soup),
            'total_counter': self._extract_total_counter(soup),
            'invoice_counter_extension': self._extract_invoice_counter_extension(soup),
            'signed_by': self._extract_signed_by(soup),
            'sdc_date_time': self._extract_sdc_date_time(soup),
            'buyer_id': self._extract_buyer_id(soup),
            'requested_by': self._extract_requested_by(soup),
            'invoice_type': self._extract_invoice_type(soup),
            'transaction_type': self._extract_transaction_type(soup),
            'status': self._extract_status(soup),
            'items': self._extract_items_from_table(soup)
        }
        
        return SerbianFiscalData(**data)
    
    def _extract_tin(self, soup: BeautifulSoup) -> str:
        """Извлечение ПИБ"""
        tin_element = soup.find('span', {'id': 'tinLabel'})
        return tin_element.get_text(strip=True) if tin_element else ""
    
    def _extract_shop_name(self, soup: BeautifulSoup) -> str:
        """Извлечение названия магазина"""
        shop_element = soup.find('span', {'id': 'shopFullNameLabel'})
        return shop_element.get_text(strip=True) if shop_element else ""
    
    def _extract_shop_address(self, soup: BeautifulSoup) -> str:
        """Извлечение адреса магазина"""
        address_element = soup.find('span', {'id': 'addressLabel'})
        return address_element.get_text(strip=True) if address_element else ""
    
    def _extract_city(self, soup: BeautifulSoup) -> str:
        """Извлечение города"""
        city_element = soup.find('span', {'id': 'cityLabel'})
        return city_element.get_text(strip=True) if city_element else ""
    
    def _extract_administrative_unit(self, soup: BeautifulSoup) -> str:
        """Извлечение општины"""
        admin_element = soup.find('span', {'id': 'administrativeUnitLabel'})
        return admin_element.get_text(strip=True) if admin_element else ""
    
    def _extract_invoice_number(self, soup: BeautifulSoup) -> str:
        """Извлечение номера чека"""
        invoice_element = soup.find('span', {'id': 'invoiceNumberLabel'})
        return invoice_element.get_text(strip=True) if invoice_element else ""
    
    def _extract_total_amount(self, soup: BeautifulSoup) -> Decimal:
        """Извлечение общей суммы"""
        total_element = soup.find('span', {'id': 'totalAmountLabel'})
        if total_element:
            amount_text = total_element.get_text(strip=True)
            # В сербском формате: 1.839,96 - точка для тысяч, запятая для десятичных
            amount_text = amount_text.replace('.', '').replace(',', '.')
            return Decimal(amount_text)
        return Decimal('0')
    
    def _extract_transaction_type_counter(self, soup: BeautifulSoup) -> int:
        """Извлечение счетчика по типу транзакции"""
        counter_element = soup.find('span', {'id': 'transactionTypeCounterLabel'})
        if counter_element:
            return int(counter_element.get_text(strip=True))
        return 0
    
    def _extract_total_counter(self, soup: BeautifulSoup) -> int:
        """Извлечение общего счетчика"""
        counter_element = soup.find('span', {'id': 'totalCounterLabel'})
        if counter_element:
            return int(counter_element.get_text(strip=True))
        return 0
    
    def _extract_invoice_counter_extension(self, soup: BeautifulSoup) -> str:
        """Извлечение расширения счетчика чека"""
        extension_element = soup.find('span', {'id': 'invoiceCounterExtensionLabel'})
        return extension_element.get_text(strip=True) if extension_element else ""
    
    def _extract_signed_by(self, soup: BeautifulSoup) -> str:
        """Извлечение подписи"""
        signed_element = soup.find('span', {'id': 'signedByLabel'})
        return signed_element.get_text(strip=True) if signed_element else ""
    
    def _extract_sdc_date_time(self, soup: BeautifulSoup) -> datetime:
        """Извлечение времени ПФР"""
        date_element = soup.find('span', {'id': 'sdcDateTimeLabel'})
        if date_element:
            date_text = date_element.get_text(strip=True)
            try:
                return datetime.strptime(date_text, "%d.%m.%Y. %H:%M:%S")
            except ValueError:
                pass
        return datetime.now()
    
    def _extract_buyer_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлечение ID покупателя"""
        buyer_element = soup.find('span', {'id': 'buyerIdLabel'})
        buyer_text = buyer_element.get_text(strip=True) if buyer_element else ""
        return buyer_text if buyer_text else None
    
    def _extract_requested_by(self, soup: BeautifulSoup) -> str:
        """Извлечение информации о том, кто затребовал"""
        requested_element = soup.find('span', {'id': 'requestedByLabel'})
        return requested_element.get_text(strip=True) if requested_element else ""
    
    def _extract_invoice_type(self, soup: BeautifulSoup) -> str:
        """Извлечение типа чека"""
        type_element = soup.find('span', {'id': 'invoiceTypeId'})
        return type_element.get_text(strip=True) if type_element else ""
    
    def _extract_transaction_type(self, soup: BeautifulSoup) -> str:
        """Извлечение типа транзакции"""
        type_element = soup.find('span', {'id': 'transactionTypeId'})
        return type_element.get_text(strip=True) if type_element else ""
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Извлечение статуса чека"""
        status_element = soup.find('label', {'id': 'invoiceStatusLabel'})
        return status_element.get_text(strip=True) if status_element else ""
    
    def _extract_items_from_table(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение товаров из таблицы после загрузки Knockout.js"""
        items = []
        
        print("🔍 Поиск товаров в HTML...")
        
        # Сохраняем HTML для отладки
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(str(soup.prettify()))
        print("💾 HTML сохранен в debug_page.html для отладки")
        
        # Метод 1: Ищем по Knockout.js биндингам
        items = self._extract_items_by_knockout_binding(soup)
        if items:
            print(f"✅ Найдено товаров через Knockout.js: {len(items)}")
            return items
        
        # Метод 2: Ищем все строки таблиц
        all_rows = soup.find_all('tr')
        print(f"📊 Найдено строк таблиц: {len(all_rows)}")
        
        # Показываем первые несколько строк для отладки
        for i, row in enumerate(all_rows[:10]):
            cells = row.find_all(['td', 'th'])
            if cells:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                print(f"  Строка {i}: {cell_texts}")
        
        for i, row in enumerate(all_rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:  # Минимум 4 колонки (название, количество, цена, сумма)
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                print(f"  🔍 Проверяем строку {i}: {cell_texts}")
                
                # Проверяем, похожа ли строка на товар
                if self._is_item_row(cell_texts):
                    print(f"  ✅ Строка {i} похожа на товар")
                    try:
                        item = self._parse_item_row(cells)
                        if item and item['name']:  # Только если есть название
                            items.append(item)
                            print(f"  ✅ Товар {len(items)}: {item['name']} - {item['quantity']} x {item['price']} = {item['sum']}")
                        else:
                            print(f"  ❌ Товар не создан или без названия")
                    except Exception as e:
                        print(f"  ❌ Ошибка парсинга строки: {e}")
                        continue
                else:
                    print(f"  ❌ Строка {i} не похожа на товар")
        
        # Метод 3: Если товары не найдены, ищем по тексту
        if not items:
            print("🔍 Товары не найдены в таблицах, ищем по тексту...")
            items = self._extract_items_by_text_search(soup)
        
        print(f"📦 Итого найдено товаров: {len(items)}")
        return items
    
    def _extract_items_by_knockout_binding(self, soup: BeautifulSoup) -> List[Dict]:
        """Поиск товаров через Knockout.js биндинги"""
        items = []
        seen_items = set()  # Для избежания дублирования
        
        # Ищем элементы с data-bind="foreach: Specifications"
        knockout_elements = soup.find_all(attrs={"data-bind": lambda x: x and "Specifications" in x})
        print(f"🔗 Найдено Knockout.js элементов: {len(knockout_elements)}")
        
        for element in knockout_elements:
            print(f"  Knockout элемент: {element.name} - {element.get('data-bind')}")
            
            # Ищем строки внутри этого элемента
            rows = element.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:  # Минимум 4 колонки
                    try:
                        item = self._parse_item_row(cells)
                        if item and item['name']:
                            # Создаем уникальный ключ для товара
                            item_key = f"{item['name']}_{item['quantity']}_{item['price']}"
                            if item_key not in seen_items:
                                items.append(item)
                                seen_items.add(item_key)
                                print(f"    ✅ Товар: {item['name']}")
                            else:
                                print(f"    ⚠️ Дублированный товар: {item['name']}")
                    except Exception as e:
                        print(f"    ❌ Ошибка: {e}")
        
        return items
    
    def _extract_items_by_text_search(self, soup: BeautifulSoup) -> List[Dict]:
        """Поиск товаров по тексту (fallback метод)"""
        items = []
        
        print("🔍 Поиск товаров по тексту...")
        
        # Ищем все элементы с текстом, содержащим числа и цены
        text_content = soup.get_text()
        
        # Ищем строки, которые могут быть товарами
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(char.isdigit() for char in line):
                # Проверяем, содержит ли строка паттерны товара
                if self._looks_like_item_line(line):
                    print(f"  📝 Возможный товар: {line[:100]}...")
                    # Пытаемся извлечь данные из строки
                    item = self._extract_item_from_line(line)
                    if item:
                        items.append(item)
                        print(f"  ✅ Добавлен товар: {item['name']}")
        
        return items
    
    def _extract_item_from_line(self, line: str) -> Optional[Dict]:
        """Извлечение товара из строки текста"""
        import re
        
        # Ищем числа в сербском формате
        numbers = re.findall(r'\d+[.,]\d+', line)
        if len(numbers) >= 3:  # Минимум количество, цена, сумма
            try:
                # Пытаемся извлечь название товара (до первого числа)
                name_match = re.match(r'^([^0-9]+)', line)
                name = name_match.group(1).strip() if name_match else "Товар"
                
                # Парсим числа
                quantity = Decimal(numbers[0].replace(',', '.'))
                price = self._parse_serbian_number(numbers[1])
                total = self._parse_serbian_number(numbers[2])
                
                # Определяем НДС по умолчанию
                nds_type = 2  # 10%
                
                return {
                    'name': name,
                    'quantity': quantity,
                    'price': price,
                    'sum': total,
                    'nds_type': nds_type,
                    'tax_base': total * Decimal('0.909'),  # Примерный расчет
                    'vat_amount': total * Decimal('0.091'),
                    'label': 'Е'
                }
            except Exception as e:
                print(f"  ❌ Ошибка извлечения товара: {e}")
                return None
        
        return None
    
    
    def _looks_like_item_line(self, line: str) -> bool:
        """Проверяет, похожа ли строка на товар"""
        # Ищем паттерны: название + количество + цена + сумма
        import re
        
        # Проверяем наличие чисел в сербском формате
        serbian_numbers = re.findall(r'\d+[.,]\d+', line)
        if len(serbian_numbers) >= 2:  # Минимум количество и цена
            return True
        
        return False
    
    def _is_item_row(self, cell_texts: List[str]) -> bool:
        """Проверяет, является ли строка товаром"""
        if len(cell_texts) < 4:  # Минимум название, количество, цена, сумма
            return False
        
        # Проверяем наличие числовых значений в колонках
        try:
            # Колонка 1 (количество) должна быть числом
            quantity = cell_texts[1].replace(',', '.')
            float(quantity)
            
            # Колонка 2 (цена) должна быть числом
            price = cell_texts[2].replace('.', '').replace(',', '.')
            float(price)
            
            # Колонка 3 (сумма) должна быть числом
            total = cell_texts[3].replace('.', '').replace(',', '.')
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
        
        print(f"    📝 Парсим товар: {name} | {quantity_text} | {unit_price_text} | {total_text}")
        
        # Парсим числовые значения
        quantity = Decimal(quantity_text.replace(',', '.')) if quantity_text else Decimal('0')
        unit_price = self._parse_serbian_number(unit_price_text)
        total = self._parse_serbian_number(total_text)
        
        # Определяем тип НДС по лейблу
        nds_type = 2  # По умолчанию 10%
        if 'Ђ' in label or '20' in label:
            nds_type = 3  # 20%
        elif 'Е' in label or '10' in label:
            nds_type = 2  # 10%
        elif 'А' in label:
            nds_type = 1  # Без НДС
        
        return {
            'name': name,
            'quantity': quantity,
            'price': unit_price,
            'sum': total,
            'nds_type': nds_type,
            'tax_base': self._parse_serbian_number(tax_base_text),
            'vat_amount': self._parse_serbian_number(vat_amount_text),
            'label': label
        }
    
    def _parse_serbian_number(self, text: str) -> Decimal:
        """Парсинг сербских чисел (1.839,96 -> 1839.96)"""
        if not text:
            return Decimal('0')
        
        # Убираем точки (разделители тысяч) и заменяем запятую на точку
        cleaned_text = text.replace('.', '').replace(',', '.')
        try:
            return Decimal(cleaned_text)
        except:
            return Decimal('0')
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SerbianToRussianConverter:
    """Конвертер сербских данных в российский формат"""
    
    def __init__(self, serbian_data: SerbianFiscalData):
        self.serbian_data = serbian_data
    
    def convert(self) -> FiscalData:
        """Конвертация сербских данных в российский формат"""
        import uuid
        import random
        
        # Генерируем случайный ID по образцу rus.json (24 символа)
        import string
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        print(f"🔧 Генерируем ID: {random_id}")
        print(f"🔧 Дата создания: {self.serbian_data.sdc_date_time}")
        
        # Создаем товары на основе извлеченных данных
        items = []
        for item_data in self.serbian_data.items:
            # Конвертируем Decimal в int (копейки)
            quantity = int(float(item_data['quantity']))  # 1.00 -> 1
            price = int(float(item_data['price']) * 100)  # 79.99 -> 7999 копеек
            sum_val = int(float(item_data['sum']) * 100)  # 79.99 -> 7999 копеек
            
            item = Item(
                name=item_data['name'],
                quantity=quantity,
                price=price,
                sum=sum_val,
                nds=item_data['nds_type'],
                paymentType=4,  # По умолчанию наличные
                productType=1  # Товар
            )
            items.append(item)
        
        # Если товары не найдены, создаем один общий товар
        if not items:
            total_cents = int(float(self.serbian_data.total_amount) * 100)
            item = Item(
                name="Товары/услуги",
                quantity=1,  # 1 товар
                price=total_cents,
                sum=total_cents,
                nds=2,  # НДС 10%
                paymentType=1,
                productType=1
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
            amountsReceiptNds=amounts_receipt_nds
        )
        
        # Создаем документ
        document = Document(receipt=receipt)
        ticket = Ticket(document=document)
        
        # Создаем фискальные данные с правильными полями
        print(f"🔧 Создаем FiscalData с ID: {random_id}")
        print(f"🔧 Создаем FiscalData с created_at: {self.serbian_data.sdc_date_time}")
        
        fiscal_data = FiscalData(ticket=ticket)
        
        print(f"🔧 FiscalData создан без ID и created_at:")
        print(f"   ID: {fiscal_data.id}")
        print(f"   Created: {fiscal_data.created_at}")
        
        # Устанавливаем значения после создания
        fiscal_data.id = random_id
        fiscal_data.created_at = self.serbian_data.sdc_date_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        print(f"🔧 FiscalData после установки значений:")
        print(f"   ID: {fiscal_data.id}")
        print(f"   Created: {fiscal_data.created_at}")
        
        return fiscal_data

def create_serbian_data_with_items():
    """Создание сербских данных с товарами вручную"""
    
    # Товары из вашего примера
    items = [
        {
            'name': 'Dečiji jog.DUO-NEO/KOM/0216130',
            'quantity': Decimal('1.00'),
            'price': Decimal('79.99'),
            'sum': Decimal('79.99'),
            'nds_type': 2,  # 10%
            'tax_base': Decimal('72.72'),
            'vat_amount': Decimal('7.27'),
            'label': 'Е'
        },
        {
            'name': 'Jogurt sa čok.i ban./KOM/0200385',
            'quantity': Decimal('1.00'),
            'price': Decimal('79.99'),
            'sum': Decimal('79.99'),
            'nds_type': 3,  # 20%
            'tax_base': Decimal('66.66'),
            'vat_amount': Decimal('13.33'),
            'label': 'Ђ'
        },
        {
            'name': 'Fil.los. sa kož./KOM/0218373',
            'quantity': Decimal('1.00'),
            'price': Decimal('1599.99'),
            'sum': Decimal('1599.99'),
            'nds_type': 2,  # 10%
            'tax_base': Decimal('1454.54'),
            'vat_amount': Decimal('145.45'),
            'label': 'Е'
        },
        {
            'name': 'Dečiji jogurt DUO-dr/KOM/0216130',
            'quantity': Decimal('1.00'),
            'price': Decimal('79.99'),
            'sum': Decimal('79.99'),
            'nds_type': 2,  # 10%
            'tax_base': Decimal('72.72'),
            'vat_amount': Decimal('7.27'),
            'label': 'Е'
        }
    ]
    
    # Создаем сербские данные
    serbian_data = SerbianFiscalData(
        tin="106884584",
        shop_name="1228831-Prodavnica br. 0156",
        shop_address="БУЛЕВАР ДЕСПОТА СТЕФАНА 99",
        city="БЕОГРАД (ПАЛИЛУЛА)",
        administrative_unit="",
        invoice_number="88856",
        total_amount=Decimal("1839.96"),
        transaction_type_counter=87369,
        total_counter=88856,
        invoice_counter_extension="",
        signed_by="",
        sdc_date_time=datetime.now(),
        buyer_id=None,
        requested_by="",
        invoice_type="",
        transaction_type="",
        status="",
        items=items
    )
    
    return serbian_data

def convert_to_russian_format(serbian_data):
    """Конвертация в российский формат"""
    
    # Создаем товары для российского формата
    items = []
    for item_data in serbian_data.items:
        item = Item(
            name=item_data['name'],
            quantity=item_data['quantity'],
            price=item_data['price'],
            sum=item_data['sum'],
            nds=item_data['nds_type'],
            payment_type="card",  # По умолчанию карта
            product_type=1  # Товар
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
        items=items
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
        print(f"🔧 Конвертируем данные...")
        print(f"   TIN: {serbian_data.tin}")
        print(f"   Shop: {serbian_data.shop_name}")
        print(f"   Total: {serbian_data.total_amount}")
        print(f"   Items: {len(serbian_data.items)}")
        
        converter = SerbianToRussianConverter(serbian_data)
        russian_data = converter.convert()
        
        print(f"✅ Конвертация завершена")
        print(f"   ID: {russian_data.id}")
        print(f"   Created: {russian_data.created_at}")
        
        # Возвращаем массив как в rus.json
        return [russian_data.model_dump(mode='json', by_alias=True)]
