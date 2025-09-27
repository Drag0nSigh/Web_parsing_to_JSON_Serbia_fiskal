#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска телеграм бота
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импортируем и запускаем бота
from bot_tg.telegram_bot import main

if __name__ == '__main__':
    # Очищаем временный файл перезапуска если он есть
    restart_file = Path("restart_bot.py")
    if restart_file.exists():
        try:
            restart_file.unlink()
            print("🧹 Очищен временный файл перезапуска")
        except:
            pass
    
    print("🤖 Запуск телеграм бота для парсинга фискальных данных...")
    print("📋 Бот будет ожидать сообщения с ссылками на сербские фискальные чеки")
    print("🔄 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        sys.exit(1)
