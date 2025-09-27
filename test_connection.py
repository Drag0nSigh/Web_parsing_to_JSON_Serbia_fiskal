#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки подключения к базе данных и Telegram API
"""

import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.db.database import db_manager

def test_database_connection():
    """Тестирование подключения к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        # Проверяем подключение
        if db_manager.check_connection():
            print("✅ Подключение к базе данных работает")
            
            # Пробуем инициализировать базу данных
            if db_manager.init_database():
                print("✅ База данных инициализирована")
                return True
            else:
                print("❌ Ошибка инициализации базы данных")
                return False
        else:
            print("❌ Не удается подключиться к базе данных")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании базы данных: {e}")
        return False

def test_telegram_token():
    """Тестирование Telegram токена"""
    print("\n🔍 Тестирование Telegram токена...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    token = os.getenv('TG_TOKEN')
    if not token:
        print("❌ TG_TOKEN не найден в переменных окружения")
        return False
    
    if len(token.split(':')) != 2:
        print("❌ Неверный формат токена. Должен быть в формате 'BOT_ID:BOT_TOKEN'")
        return False
    
    print("✅ Токен найден и имеет правильный формат")
    return True

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование подключений...")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Тестируем Telegram токен
    telegram_ok = test_telegram_token()
    
    # Тестируем базу данных
    db_ok = test_database_connection()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Telegram токен: {'✅ OK' if telegram_ok else '❌ Ошибка'}")
    print(f"   База данных: {'✅ OK' if db_ok else '❌ Ошибка'}")
    
    if telegram_ok and db_ok:
        print("\n🎉 Все тесты пройдены! Бот готов к запуску.")
        return True
    else:
        print("\n⚠️ Есть проблемы, которые нужно исправить перед запуском бота.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
