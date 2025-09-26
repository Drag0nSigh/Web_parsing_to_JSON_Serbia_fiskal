#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт инициализации базы данных
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.db.database import db_manager

def main():
    """Инициализация базы данных"""
    print("🚀 Инициализация базы данных...")
    
    try:
        # Проверяем подключение
        if not db_manager.check_connection():
            print("❌ Не удалось подключиться к базе данных")
            return False
        
        # Инициализируем базу данных
        if db_manager.init_database():
            print("✅ База данных успешно инициализирована")
            return True
        else:
            print("❌ Ошибка инициализации базы данных")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False
    
    finally:
        # Закрываем соединение
        db_manager.close()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
