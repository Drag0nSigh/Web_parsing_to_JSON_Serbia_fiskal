#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from parser.fiscal_parser import parse_serbian_fiscal_url
from utils.timing_decorator import timing_decorator, async_timing_decorator
from db.utils import log_user_request, init_database
from .admin_commands import (
    admin_start, admin_logs, admin_logs_date, admin_users, 
    admin_test, admin_status, admin_stats, is_admin
)

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем папку для логов
log_dir = Path("log")
log_dir.mkdir(exist_ok=True)

# Получаем токен бота
TG_TOKEN = os.getenv('TG_TOKEN')
if not TG_TOKEN:
    raise ValueError("TG_TOKEN не найден в файле .env")

@timing_decorator
def is_url(text: str) -> bool:
    """Проверяет, является ли текст URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))

@timing_decorator
def log_request(user_id: int, username: str, status: str = 'success', 
               error_message: str = None) -> None:
    """Записывает информацию о запросе в базу данных"""
    try:
        # Логируем в базу данных
        log_user_request(
            user_id=user_id,
            username=username,
            status=status,
            error_message=error_message
        )
        
        # Также сохраняем в файл для совместимости
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"requests_log_{date_str}.txt"
        log_file = log_dir / log_filename
        
        status_emoji = "✅" if status == 'success' else "❌"
        log_entry = f"{timestamp} | ID: {user_id} | @{username} | {status_emoji} {status}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        logger.error(f"❌ Ошибка логирования запроса: {e}")

@async_timing_decorator
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Добро пожаловать в бот для парсинга фискальных данных!\n\n"
        "📋 Отправьте мне ссылку на сербский фискальный чек, и я верну JSON в российском формате.\n\n"
        "🔗 Бот принимает только ссылки!\n\n"
        "💡 Пример ссылки:\n"
        "https://suf.purs.gov.rs/v/?vl=..."
    )

@async_timing_decorator
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех сообщений"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    message_text = update.message.text.strip()
    
    # Проверяем, является ли сообщение URL
    if not is_url(message_text):
        await update.message.reply_text(
            "❌ Сообщение не является ссылкой!\n\n"
            "🔗 Бот принимает только ссылки на сербские фискальные чеки."
        )
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "⏳ Обрабатываю ссылку...\n"
        "🔄 Парсинг может занять некоторое время..."
    )
    
    try:
        # Парсим URL с созданием нового драйвера при каждом запросе
        logger.info(f"Парсинг URL: {message_text}")
        result = parse_serbian_fiscal_url(message_text, headless=True)
        
        # Записываем в лог
        log_request(
            user_id=user_id, 
            username=username, 
            status='success'
        )
        
        # Отправляем результат
        await processing_msg.edit_text(
            "✅ Парсинг завершен!\n\n"
            "📄 Отправляю JSON файл..."
        )
        
        # Отправляем JSON как файл
        json_text = json.dumps(result, ensure_ascii=False, indent=2)
        
        await update.message.reply_document(
            document=json_text.encode('utf-8'),
            filename=f"fiscal_data_{datetime.now().strftime('%d%m%y_%H-%M-%S')}.json",
            caption="📄 JSON данные в российском формате"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        
        # Логируем ошибку
        log_request(
            user_id=user_id,
            username=username,
            status='error',
            error_message=str(e)
        )
        
        await processing_msg.edit_text(
            f"❌ Ошибка при обработке ссылки:\n\n"
            f"🔍 {str(e)}\n\n"
            "Попробуйте другую ссылку или обратитесь к администратору."
        )

@async_timing_decorator
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла внутренняя ошибка бота.\n"
            "Попробуйте позже или обратитесь к администратору."
        )

@timing_decorator
def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Запуск телеграм бота...")
    
    # Инициализируем базу данных
    logger.info("🔧 Инициализация базы данных...")
    if not init_database():
        logger.error("❌ Не удалось инициализировать базу данных")
        logger.warning("⚠️ Бот будет работать без базы данных (только файловые логи)")
    else:
        logger.info("✅ База данных инициализирована")
    
    # Создаем приложение
    application = Application.builder().token(TG_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Административные команды
    application.add_handler(CommandHandler("admin_start", admin_start))
    application.add_handler(CommandHandler("admin_logs", admin_logs))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_test", admin_test))
    application.add_handler(CommandHandler("admin_status", admin_status))
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    
    # Обработчик для команд с датой (admin_logs_YYYY-MM-DD)
    application.add_handler(MessageHandler(filters.Regex(r'^/admin_logs_\d{4}-\d{2}-\d{2}$'), admin_logs_date))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен и ожидает сообщения...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
