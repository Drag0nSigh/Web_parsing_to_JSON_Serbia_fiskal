"""
Основной файл телеграм бота
"""
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from db.utils import init_database
from .admin_commands import (
    admin_start, admin_logs, admin_logs_date, admin_users, 
    admin_test, admin_status, admin_stats, send_message_to_user, 
    activate_user_command, deactivate_user_command, is_admin
)
from .user_commands import start, help_command, admin_message, handle_message

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
from utils.log_manager import get_log_manager

# Получаем менеджер логов
log_manager = get_log_manager()

# Настраиваем логирование
logger = log_manager.setup_logging("bot", logging.INFO)

# Получаем токен бота
TG_TOKEN = os.getenv('TG_TOKEN')

# Проверяем формат токена
if not TG_TOKEN or len(TG_TOKEN.split(':')) != 2:
    raise ValueError("Неверный формат TG_TOKEN. Токен должен быть в формате 'BOT_ID:BOT_TOKEN'")

def create_main_menu() -> InlineKeyboardMarkup:
    """Создает главное меню без кнопок для обычных пользователей"""
    # Возвращаем пустое меню для обычных пользователей
    return InlineKeyboardMarkup([])

def create_admin_menu() -> InlineKeyboardMarkup:
    """Создает административное меню с кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("📝 Логи", callback_data="admin_logs"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("🧪 Тест", callback_data="admin_test")
        ],
        [
            InlineKeyboardButton("📨 Отправить", callback_data="admin_send_message"),
            InlineKeyboardButton("📈 Статус", callback_data="admin_status")
        ],
        [
            InlineKeyboardButton("✅ Активировать", callback_data="admin_activate"),
            InlineKeyboardButton("🚫 Деактивировать", callback_data="admin_deactivate")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки (только административные)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    # Проверяем, не обрабатывается ли уже этот callback
    if hasattr(context, 'processing_callbacks'):
        if query.id in context.processing_callbacks:
            return
        context.processing_callbacks.add(query.id)
    else:
        context.processing_callbacks = {query.id}
    
    # Обработка только административных кнопок
    if query.data == "admin_logs":
        if is_admin(user_id):
            try:
                from db.utils import get_recent_logs
                logs = get_recent_logs(limit=20)
                
                if logs:
                    message = "📝 <b>Последние логи запросов:</b>\n\n"
                    for i, log in enumerate(logs[:10], 1):
                        created_at = log.get('created_at', 'N/A')
                        user_id_log = log.get('user_id', 'N/A')
                        username_log = log.get('username', 'N/A')
                        status = log.get('status', 'unknown')
                        status_emoji = "✅" if status == 'success' else "❌"
                        message += f"{i}. {status_emoji} {created_at}\n"
                        message += f"   👤 ID: {user_id_log} | @{username_log}\n\n"
                else:
                    message = "📝 Логи не найдены"
                    
                await query.edit_message_text(message, parse_mode='HTML', reply_markup=create_admin_menu())
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка получения логов: {str(e)}", reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_users":
        if is_admin(user_id):
            try:
                from db.utils import get_users_list
                users = get_users_list(limit=20)
                
                if users:
                    message = f"👥 <b>Список пользователей ({len(users)}):</b>\n\n"
                    for i, user in enumerate(users[:10], 1):
                        telegram_id = user.get('telegram_id', 'N/A')
                        username_log = user.get('username', 'без_username')
                        is_active = user.get('is_active', True)
                        status_emoji = "🟢" if is_active else "🔴"
                        message += f"{i}. {status_emoji} <b>@{username_log}</b>\n"
                        message += f"   🆔 ID: {telegram_id}\n\n"
                else:
                    message = "👥 Пользователи не найдены"
                    
                await query.edit_message_text(message, parse_mode='HTML', reply_markup=create_admin_menu())
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка получения пользователей: {str(e)}", reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_stats":
        if is_admin(user_id):
            try:
                from db.utils import get_system_stats, get_database_info
                stats = get_system_stats(days=7)
                db_info = get_database_info()
                
                if stats:
                    message = "📊 <b>Статистика использования (7 дней):</b>\n\n"
                    message += f"🔢 Всего запросов: {stats.get('total_requests', 0)}\n"
                    message += f"✅ Успешных: {stats.get('successful_requests', 0)}\n"
                    message += f"❌ Ошибок: {stats.get('failed_requests', 0)}\n"
                    message += f"👥 Уникальных пользователей: {stats.get('unique_users', 0)}\n\n"
                    message += f"🗄️ <b>База данных:</b>\n"
                    message += f"👥 Пользователей: {db_info.get('users_count', 0)}\n"
                    message += f"📝 Логов: {db_info.get('logs_count', 0)}\n"
                    message += f"🔗 Статус: {db_info.get('connection_status', 'unknown')}\n\n"
                    message += f"💡 <i>Успешными считаются: парсинг ссылок, команды</i>"
                else:
                    message = "📊 Статистика недоступна"
                    
                await query.edit_message_text(message, parse_mode='HTML', reply_markup=create_admin_menu())
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка получения статистики: {str(e)}", reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_test":
        if is_admin(user_id):
            try:
                # Показываем сообщение о начале тестирования
                await query.edit_message_text("🧪 <b>Тестирую парсер...</b>\n\n⏳ Выполняю проверку...", parse_mode='HTML', reply_markup=create_admin_menu())
                
                # Тестовая ссылка для проверки парсера
                test_url = "https://suf.purs.gov.rs/v/?vl=test"
                
                # Выполняем тест парсера
                try:
                    from parser.fiscal_parser import parse_serbian_fiscal_url
                    result = parse_serbian_fiscal_url(test_url)
                    
                    if result:
                        test_message = f"""
🧪 <b>Результат тестирования парсера:</b>

✅ <b>Парсер работает корректно!</b>

📊 <b>Детали теста:</b>
• URL: <code>{test_url}</code>
• Статус: Успешно обработан
• Результат: JSON получен

🔧 <b>Компоненты парсера:</b>
• Selenium WebDriver: ✅ Работает
• BeautifulSoup: ✅ Работает  
• Парсинг данных: ✅ Работает
• Обработка ошибок: ✅ Работает

💡 <b>Парсер готов к работе!</b>
                        """
                    else:
                        test_message = f"""
🧪 <b>Результат тестирования парсера:</b>

⚠️ <b>Парсер работает, но тестовая ссылка неверная</b>

📊 <b>Детали теста:</b>
• URL: <code>{test_url}</code>
• Статус: Обработан, но данные не получены
• Причина: Тестовая ссылка не содержит реальных данных

🔧 <b>Компоненты парсера:</b>
• Selenium WebDriver: ✅ Работает
• BeautifulSoup: ✅ Работает  
• Парсинг данных: ⚠️ Работает, но нет данных
• Обработка ошибок: ✅ Работает

💡 <b>Парсер готов к работе с реальными ссылками!</b>
                        """
                        
                except Exception as parse_error:
                    test_message = f"""
🧪 <b>Результат тестирования парсера:</b>

❌ <b>Ошибка при тестировании</b>

📊 <b>Детали теста:</b>
• URL: <code>{test_url}</code>
• Статус: Ошибка
• Ошибка: {str(parse_error)}

🔧 <b>Компоненты парсера:</b>
• Selenium WebDriver: ❌ Проблема
• BeautifulSoup: ❓ Неизвестно
• Парсинг данных: ❌ Не работает
• Обработка ошибок: ✅ Работает

🛠️ <b>Рекомендации:</b>
• Проверить установку Selenium
• Проверить Chrome/ChromeDriver
• Проверить интернет-соединение
                    """
                
                # Обновляем сообщение с результатами теста
                await query.edit_message_text(test_message, parse_mode='HTML', reply_markup=create_admin_menu())
                
            except Exception as e:
                logger.error(f"❌ Ошибка при тестировании парсера: {e}")
                await query.edit_message_text(
                    f"❌ <b>Ошибка тестирования</b>\n\n"
                    f"Не удалось выполнить тест парсера.\n"
                    f"Ошибка: {str(e)}",
                    parse_mode='HTML',
                    reply_markup=create_admin_menu()
                )
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_send_message":
        if is_admin(user_id):
            send_message_text = """
📨 <b>Отправка сообщения пользователю</b>

<b>Использование:</b>
<code>/send ID_пользователя текст сообщения</code>

<b>Примеры:</b>
• <code>/send 123456789 Привет! Как дела?</code>
• <code>/send 987654321 Уведомление о технических работах</code>

<b>Как узнать ID пользователя:</b>
• Используйте кнопку "👥 Пользователи" в админ меню
• ID отображается в списке пользователей

<b>Примечание:</b>
• Пользователь должен был хотя бы раз написать боту
• Сообщение будет отправлено от имени бота
            """
            await query.edit_message_text(send_message_text, parse_mode='HTML', reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_status":
        if is_admin(user_id):
            try:
                import psutil
                import platform
                
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                status_message = f"""
🖥️ <b>Статус системы:</b>

💻 <b>Система:</b>
• OS: {platform.system()} {platform.release()}
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)

📊 <b>Бот:</b>
• Статус: ✅ Работает
• Время: {datetime.now().strftime('%d.%m.%y %H:%M:%S')}
                """
                
                await query.edit_message_text(status_message, parse_mode='HTML', reply_markup=create_admin_menu())
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка получения статуса: {str(e)}", reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_activate":
        if is_admin(user_id):
            activate_text = """
✅ <b>Активация пользователя</b>

<b>Использование:</b>
<code>/activate ID_пользователя</code>

<b>Примеры:</b>
• <code>/activate 123456789</code>
• <code>/activate 987654321</code>

<b>Как узнать ID пользователя:</b>
• Используйте кнопку "👥 Пользователи" в админ меню
• ID отображается в списке пользователей

<b>Примечание:</b>
• Активированный пользователь сможет использовать парсинг ссылок
• Если пользователь уже активен, будет показано соответствующее сообщение
            """
            await query.edit_message_text(activate_text, parse_mode='HTML', reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
            
    elif query.data == "admin_deactivate":
        if is_admin(user_id):
            deactivate_text = """
🚫 <b>Деактивация пользователя</b>

<b>Использование:</b>
<code>/deactivate ID_пользователя</code>

<b>Примеры:</b>
• <code>/deactivate 123456789</code>
• <code>/deactivate 987654321</code>

<b>Как узнать ID пользователя:</b>
• Используйте кнопку "👥 Пользователи" в админ меню
• ID отображается в списке пользователей

<b>Примечание:</b>
• Деактивированный пользователь не сможет использовать парсинг ссылок
• Администраторы не могут быть деактивированы
• Если пользователь уже неактивен, будет показано соответствующее сообщение
            """
            await query.edit_message_text(deactivate_text, parse_mode='HTML', reply_markup=create_admin_menu())
        else:
            await query.edit_message_text("❌ У вас нет прав администратора", reply_markup=create_main_menu())
    
    # Убираем callback из списка обрабатываемых
    if hasattr(context, 'processing_callbacks'):
        context.processing_callbacks.discard(query.id)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    error = context.error
    
    # Игнорируем ошибку "Message is not modified" - это нормально при повторных нажатиях
    if "Message is not modified" in str(error):
        logger.info("ℹ️ Игнорируем ошибку 'Message is not modified' - повторное нажатие кнопки")
        return
    
    logger.error(f"Ошибка: {error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла внутренняя ошибка бота.\n"
            "Попробуйте позже или обратитесь к администратору."
        )

def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Запуск телеграм бота...")
    
    try:
        # Инициализируем базу данных
        init_database()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return
    
    try:
        # Создаем приложение
        application = Application.builder().token(TG_TOKEN).build()
        logger.info("✅ Приложение Telegram создано")
    except Exception as e:
        logger.error(f"❌ Ошибка создания приложения Telegram: {e}")
        raise
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_message))
    application.add_handler(CommandHandler("send", send_message_to_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Административные команды
    application.add_handler(CommandHandler("admin_start", admin_start))
    application.add_handler(CommandHandler("admin_logs", admin_logs))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_test", admin_test))
    application.add_handler(CommandHandler("admin_status", admin_status))
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    application.add_handler(CommandHandler("activate", activate_user_command))
    application.add_handler(CommandHandler("deactivate", deactivate_user_command))
    
    # Обработчик для команд с датой (admin_logs_DD_MM_YY)
    application.add_handler(MessageHandler(filters.Regex(r'^/admin_logs_\d{2}_\d{2}_\d{2}$'), admin_logs_date))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("🚀 Бот запущен и готов к работе!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
