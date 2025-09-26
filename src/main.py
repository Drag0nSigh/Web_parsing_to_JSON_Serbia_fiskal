"""
Основной файл для парсинга сербских фискальных данных по URL
"""
import json
import sys
from pathlib import Path
from parser.fiscal_parser import parse_serbian_fiscal_url
from utils.timing_decorator import timing_decorator


@timing_decorator
def main():
    """Основная функция"""
    
    # URL для парсинга (можно передать как аргумент командной строки)
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # URL по умолчанию из примера
        url = "https://suf.purs.gov.rs/v/?vl=AzdWVDYyRUM0N1ZUNjJFQzQYWwEASVUBAHDBGAEAAAAAAAABmOyyJXMAAAAdrdjynx8FFJ7vKJSEWHehCSexnfVJwleCdnX8WapD%2FVqiutLId1kOu75ZXt4Z%2Bsp4oPEXjlYGf0jXnO6%2FcXPw%2FPXq9hZr9uVlrxjhiEVvc44J3xYEaqN2AGIwBxT%2Bco7LOqgAfE6PBUeQlA49tC%2FCvCkGuiVwfXwQfXAHyhDIs3Q29%2FfrLFsGoTpXECXvyKW%2FAg%2BxTXUFlO1zSxraDy2PbDNA%2FYSEYknv0LxtxUxuMU6FUL0fOXGM%2BmXcfYzRkDkjomzsdpiFGzuN9nRThzv16Q4S%2B9aznut5Fb2LWB85BaH4y11GtXMwubfQNzsdUpJZObMDZXcRx4V8tefqUmGlai%2FgEeT6FSrjHMGEP62UgDtokyrzuCqNeMz6JkZuHxE%2FqkLxZnYGwGUx5nRpiGEME1UyLQNUcWFsQgkJiyvWL3FpZsuRjXahZiNM5glVo1bbeISMK8%2BO8BsTPSHAg0jZkGpvi9OOT4qY8T0Zf1OMG4BnVTNM28h5ZMqobV8pjydfj%2BJtvsaDuNdv5C4Nhj3IC%2BaLeQdLFoL%2FfkA2%2F50HWUCi8KWMLVQHwYbJftNfYjPhjlrmbgG3FuDTWPM%2Bakut5GIUu4D8d1wmpqgQBenYX2qnqmcWhfNQu%2FBHz1KhizKvh2NLz%2FjWWiPicWVVM8H2cdU%2BGy4qdKkdk0WKiEtK362QBJnPpz%2BiUEFBoR6osNg%3D"
    
    print(f"🔍 Парсинг URL: {url}")
    print("🚀 Запуск парсера...")
    
    try:
        # Парсим данные
        result = parse_serbian_fiscal_url(url, headless=True)
        
        # Сохраняем результат в JSON
        output_file = Path("output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Данные успешно обработаны и сохранены в {output_file}")
        
        # Выводим краткую информацию
        receipt = result[0]['ticket']['document']['receipt']
        print(f"\n📊 Результат парсинга:")
        print(f"   Номер чека: {receipt['fiscalDocumentNumber']}")
        print(f"   Сумма: {receipt['totalSum']}")
        print(f"   Количество товаров: {len(receipt['items'])}")
        print(f"   Организация: {receipt['user']}")
        print(f"   Дата: {receipt['dateTime']}")
        
        # Выводим товары
        if receipt['items']:
            print(f"\n🛒 Товары:")
            for i, item in enumerate(receipt['items'], 1):
                print(f"   {i}. {item['name']} - {item['quantity']} шт. x {item['price']} = {item['sum']}")
        
        print(f"\n📄 Полный результат сохранен в {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при обработке данных: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
