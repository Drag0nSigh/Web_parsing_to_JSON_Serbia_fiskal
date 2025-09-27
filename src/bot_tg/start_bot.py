#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска телеграм бота
"""

import sys
import os
import logging
from pathlib import Path
# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.log_manager import get_log_manager

# Получаем менеджер логов
log_manager = get_log_manager()

# Настраиваем логирование
logger = log_manager.setup_logging("startup", logging.INFO)

# Импортируем и запускаем бота
from bot_tg.telegram_bot import main

if __name__ == '__main__':
    # Очищаем временный файл перезапуска если он есть
    restart_file = Path("restart_bot.py")
    if restart_file.exists():
        try:
            restart_file.unlink()
            logger.info("🧹 Очищен временный файл перезапуска")
        except:
            pass
    
    logger.info("🤖 Запуск телеграм бота для парсинга фискальных данных...")
    logger.info("📋 Бот будет ожидать сообщения с ссылками на сербские фискальные чеки")
    logger.info("🔄 Для остановки нажмите Ctrl+C")
    logger.info("-" * 50)
    
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"\n❌ Ошибка при запуске бота: {e}")
        sys.exit(1)
