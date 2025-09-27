#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Административные команды для телеграм бота
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from db.utils import get_recent_logs, get_users_list, get_system_stats, get_database_info, get_request_logs, log_message, get_username_by_id, activate_user, deactivate_user, is_user_active

# Настройка логирования
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()


def format_datetime(dt_string: str) -> str:
    """Форматирование даты и времени в формат ДД.ММ.ГГ ЧЧ:ММ:СС"""
    if not dt_string or dt_string == 'N/A':
        return 'N/A'
    
    try:
        # Парсим ISO формат
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%y %H:%M:%S')
    except (ValueError, AttributeError):
        return dt_string

# ID администратора
admin_id = int(os.getenv('ADMIN_ID', '0'))

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == admin_id

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_start - приветствие для администратора"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(f"User {update.effective_user.id} is not admin, admin_id: {admin_id}")
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    # Импортируем функцию создания админ меню
    from .telegram_bot import create_admin_menu
    
    admin_commands = """
🔧 <b>Административная панель</b>

📊 <b>Доступные функции:</b>
• Просмотр логов запросов
• Управление пользователями
• Статистика использования
• Мониторинг системы
• Тестирование парсера
• Перезапуск бота

💡 <b>Используйте кнопки ниже для быстрого доступа к функциям</b>
    """
    
    await update.message.reply_text(admin_commands, parse_mode='HTML', reply_markup=create_admin_menu())

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_logs - получение всех логов"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        # Получаем последние 50 логов
        logs = get_recent_logs(limit=50)
        
        if not logs:
            await update.message.reply_text("📝 Логи не найдены")
            return
        
        # Формируем сообщение
        message = "📝 **Последние логи запросов:**\n\n"
        
        for i, log in enumerate(logs[:20], 1):  # Показываем только первые 20
            created_at = format_datetime(log.get('created_at', 'N/A'))
            user_id = log.get('user_id', 'N/A')
            username = log.get('username', 'N/A')
            status = log.get('status', 'unknown')
            error_message = log.get('error_message', '')
            
            status_emoji = "✅" if status == 'success' else "❌"
            message += f"{i}. {status_emoji} {created_at}\n"
            message += f"   👤 ID: {user_id} | @{username}\n"
            if error_message:
                message += f"   ❌ Ошибка: {error_message[:50]}...\n\n"
            else:
                message += f"   📝 Статус: {status}\n\n"
        
        if len(logs) > 20:
            message += f"... и еще {len(logs) - 20} записей"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения логов: {str(e)}")

async def admin_logs_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_logs_DD_MM_YY - получение логов за определенную дату"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        # Извлекаем дату из команды
        command_text = update.message.text
        date_str = command_text.replace('/admin_logs_', '')
        
        # Парсим дату в формате DD_MM_YY
        try:
            date_obj = datetime.strptime(date_str, '%d_%m_%y')
            # Преобразуем в ISO формат для поиска в БД
            iso_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            await update.message.reply_text("❌ Неверный формат даты. Используйте: /admin_logs_DD_MM_YY")
            return
        
        # Получаем логи за указанную дату
        from datetime import timedelta
        
        # Создаем диапазон дат (с 00:00:00 до 23:59:59)
        date_start = datetime.combine(date_obj, datetime.min.time())
        date_end = datetime.combine(date_obj, datetime.max.time())
        
        logs = get_request_logs(
            limit=100,
            date_from=date_start,
            date_to=date_end
        )
        
        if not logs:
            await update.message.reply_text(f"📝 Логи за {date_str} не найдены")
            return
        
        # Формируем сообщение
        message = f"📝 **Логи за {date_str} ({len(logs)} записей):**\n\n"
        
        for i, log in enumerate(logs[:20], 1):  # Показываем только первые 20
            created_at = format_datetime(log.get('created_at', 'N/A'))
            user_id = log.get('user_id', 'N/A')
            username = log.get('username', 'N/A')
            status = log.get('status', 'unknown')
            error_message = log.get('error_message', '')
            
            status_emoji = "✅" if status == 'success' else "❌"
            message += f"{i}. {status_emoji} {created_at}\n"
            message += f"   👤 ID: {user_id} | @{username}\n"
            if error_message:
                message += f"   ❌ Ошибка: {error_message[:50]}...\n\n"
            else:
                message += f"   📝 Статус: {status}\n\n"
        
        if len(logs) > 20:
            message += f"... и еще {len(logs) - 20} записей"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения логов за дату: {str(e)}")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_users - получение списка пользователей"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        # Получаем список пользователей
        users = get_users_list(limit=100)
        
        if not users:
            await update.message.reply_text("👥 Пользователи не найдены")
            return
        
        # Формируем сообщение
        message = f"👥 **Список пользователей ({len(users)}):**\n\n"
        
        for i, user in enumerate(users[:20], 1):  # Показываем только первых 20
            telegram_id = user.get('telegram_id', 'N/A')
            username = user.get('username', 'без_username')
            created_at = format_datetime(user.get('created_at', 'N/A'))
            last_activity = format_datetime(user.get('last_activity', 'N/A'))
            is_active = user.get('is_active', True)
            
            status_emoji = "🟢" if is_active else "🔴"
            
            message += f"{i}. {status_emoji} **@{username}**\n"
            message += f"   🆔 ID: {telegram_id}\n"
            message += f"   📅 Регистрация: {created_at}\n"
            message += f"   🕐 Активность: {last_activity}\n\n"
        
        if len(users) > 20:
            message += f"... и еще {len(users) - 20} пользователей"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения пользователей: {str(e)}")


async def admin_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_test - тест работоспособности"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        # Тестируем парсер
        from parser.fiscal_parser import parse_serbian_fiscal_url
        
        test_url = "https://suf.purs.gov.rs/v/?vl=AzdWVDYyRUM0N1ZUNjJFQzQYWwEASVUBAHDBGAEAAAAAAAABmOyyJXMAAAAdrdjynx8FFJ7vKJSEWHehCSexnfVJwleCdnX8WapD%2FVqiutLId1kOu75ZXt4Z%2Bsp4oPEXjlYGf0jXnO6%2FcXPw%2FPXq9hZr9uVlrxjhiEVvc44J3xYEaqN2AGIwBxT%2Bco7LOqgAfE6PBUeQlA49tC%2FCvCkGuiVwfXwQfXAHyhDIs3Q29%2FfrLFsGoTpXECXvyKW%2FAg%2BxTXUFlO1zSxraDy2PbDNA%2FYSEYknv0LxtxUxuMU6FUL0fOXGM%2BmXcfYzRkDkjomzsdpiFGzuN9nRThzv16Q4S%2B9aznut5Fb2LWB85BaH4y11GtXMwubfQNzsdUpJZObMDZXcRx4V8tefqUmGlai%2FgEeT6FSrjHMGEP62UgDtokyrzuCqNeMz6JkZuHxE%2FqkLxZnYGwGUx5nRpiGEME1UyLQNUcWFsQgkJiyvWL3FpZsuRjXahZiNM5glVo1bbeISMK8%2BO8BsTPSHAg0jZkGpvi9OOT4qY8T0Zf1OMG4BnVTNM28h5ZMqobV8pjydfj%2BJtvsaDuNdv5C4Nhj3IC%2BaLeQdLFoL%2FfkA2%2F50HWUCi8KWMLVQHwYbJftNfYjPhjlrmbgG3FuDTWPM%2Bakut5GIUu4D8d1wmpqgQBenYX2qnqmcWhfNQu%2FBHz1KhizKvh2NLz%2FjWWiPicWVVM8H2cdU%2BGy4qdKkdk0WKiEtK362QBJnPpz%2BiUEFBoR6osNg%3D"
        
        await update.message.reply_text("🧪 Тестирую парсер...")
        result = parse_serbian_fiscal_url(test_url, headless=True)
        
        if result and len(result) > 0:
            await update.message.reply_text("✅ Парсер работает корректно")
        else:
            await update.message.reply_text("❌ Парсер вернул пустой результат")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при тестировании: {str(e)}")

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_status - статус системы"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        import psutil
        import platform
        
        # Информация о системе
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Информация о логах
        log_dir = Path("/app/log")
        log_count = len(list(log_dir.glob("requests_log_*.txt"))) if log_dir.exists() else 0
        
        status_message = f"""
🖥️ <b>Статус системы:</b>

💻 <b>Система:</b>
• OS: {platform.system()} {platform.release()}
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)

📊 <b>Бот:</b>
• Статус: ✅ Работает
• Логов: {log_count} файлов
• Время: {datetime.now().strftime('%d.%m.%y %H:%M:%S')}
        """
        
        await update.message.reply_text(status_message, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении статуса: {str(e)}")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_stats - статистика использования"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        # Получаем статистику за последние 7 дней
        stats = get_system_stats(days=7)
        db_info = get_database_info()
        
        if not stats:
            await update.message.reply_text("📊 Статистика недоступна")
            return
        
        # Формируем сообщение
        message = "📊 **Статистика использования (7 дней):**\n\n"
        
        # Общая статистика
        message += f"📈 **Общие показатели:**\n"
        message += f"   🔢 Всего запросов: {stats.get('total_requests', 0)}\n"
        message += f"   ✅ Успешных: {stats.get('successful_requests', 0)}\n"
        message += f"   ❌ Ошибок: {stats.get('failed_requests', 0)}\n"
        message += f"   👥 Уникальных пользователей: {stats.get('unique_users', 0)}\n\n"
        message += f"   💡 <i>Успешными считаются: парсинг ссылок, команды</i>\n\n"
        
        # Статистика по дням
        daily_stats = stats.get('daily_stats', [])
        if daily_stats:
            message += f"📅 **По дням:**\n"
            for day_stat in daily_stats[:5]:  # Показываем только последние 5 дней
                date = day_stat.get('date', 'N/A')
                # Преобразуем дату в формат ДД.ММ.ГГ
                if date != 'N/A':
                    try:
                        date_obj = datetime.fromisoformat(date)
                        date = date_obj.strftime('%d.%m.%y')
                    except (ValueError, AttributeError):
                        pass
                requests = day_stat.get('total_requests', 0)
                users = day_stat.get('unique_users', 0)
                
                message += f"   {date}: {requests} запросов, {users} пользователей\n"
        
        # Информация о базе данных
        message += f"\n🗄️ **База данных:**\n"
        message += f"   👥 Пользователей: {db_info.get('users_count', 0)}\n"
        message += f"   📝 Логов: {db_info.get('logs_count', 0)}\n"
        message += f"   🔗 Статус: {db_info.get('connection_status', 'unknown')}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статистики: {str(e)}")

async def send_message_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /send - отправка сообщения пользователю по ID"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    # Проверяем права администратора
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    # Получаем аргументы команды
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📨 <b>Отправка сообщения пользователю</b>\n\n"
            "Использование: <code>/send ID_пользователя текст сообщения</code>\n\n"
            "Пример: <code>/send 123456789 Привет! Как дела?</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        # Извлекаем ID пользователя и текст сообщения
        target_user_id = int(context.args[0])
        message_text = ' '.join(context.args[1:])
        target_username = get_username_by_id(target_user_id)
        
        # Отправляем сообщение пользователю
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📨 <b>Сообщение от администратора:</b>\n\n{message_text}",
            parse_mode='HTML'
        )
        
        # Логируем сообщение в базу данных
        log_message(user_id, target_user_id, username, f"{target_username}", 'admin_to_user', 'admin_response')
        
        # Подтверждаем отправку администратору
        await update.message.reply_text(
            f"✅ <b>Сообщение отправлено!</b>\n\n"
            f"👤 <b>Получатель:</b> ID {target_user_id}\n"
            f"📝 <b>Текст:</b> {message_text}",
            parse_mode='HTML'
        )
        
        # Логируем отправку сообщения
        logger.info(f"📨 Админ {username} (ID: {user_id}) отправил сообщение пользователю {target_user_id}: {message_text}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка в ID пользователя</b>\n\n"
            "ID должен быть числом.\n"
            "Пример: <code>/send 123456789 Привет!</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        error_msg = str(e)
        if "chat not found" in error_msg.lower():
            await update.message.reply_text(
                f"❌ <b>Пользователь не найден</b>\n\n"
                f"Пользователь с ID {target_user_id} не найден или не писал боту.\n"
                f"Убедитесь, что ID правильный."
            )
        elif "blocked" in error_msg.lower():
            await update.message.reply_text(
                f"❌ <b>Пользователь заблокировал бота</b>\n\n"
                f"Пользователь с ID {target_user_id} заблокировал бота."
            )
        else:
            await update.message.reply_text(
                f"❌ <b>Ошибка отправки сообщения</b>\n\n"
                f"Ошибка: {error_msg}"
            )
        logger.error(f"❌ Ошибка отправки сообщения админом {username}: {e}")


async def activate_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /activate - активация пользователя"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    # Проверяем права администратора
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    # Получаем аргументы команды
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "✅ <b>Активация пользователя</b>\n\n"
            "Использование: <code>/activate ID_пользователя</code>\n\n"
            "Пример: <code>/activate 123456789</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        # Извлекаем ID пользователя
        target_user_id = int(context.args[0])
        target_username = get_username_by_id(target_user_id)
        
        # Проверяем текущий статус
        current_status = is_user_active(target_user_id)
        
        if current_status:
            await update.message.reply_text(
                f"ℹ️ <b>Пользователь уже активен</b>\n\n"
                f"👤 <b>Пользователь:</b> @{target_username} (ID: {target_user_id})\n"
                f"✅ <b>Статус:</b> Активен",
                parse_mode='HTML'
            )
            return
        
        # Активируем пользователя
        success = activate_user(target_user_id)
        
        if success:
            # Логируем действие
            log_message(user_id, target_user_id, username, target_username, 'admin_action', 'user_activated')
            
            await update.message.reply_text(
                f"✅ <b>Пользователь активирован!</b>\n\n"
                f"👤 <b>Пользователь:</b> @{target_username} (ID: {target_user_id})\n"
                f"🔄 <b>Статус:</b> Неактивен → Активен",
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Админ {username} (ID: {user_id}) активировал пользователя {target_username} (ID: {target_user_id})")
        else:
            await update.message.reply_text(
                f"❌ <b>Ошибка активации пользователя</b>\n\n"
                f"Пользователь с ID {target_user_id} не найден или произошла ошибка.",
                parse_mode='HTML'
            )
        
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка в ID пользователя</b>\n\n"
            "ID должен быть числом.\n"
            "Пример: <code>/activate 123456789</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка активации пользователя</b>\n\n"
            f"Ошибка: {str(e)}"
        )
        logger.error(f"❌ Ошибка активации пользователя админом {username}: {e}")


async def deactivate_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /deactivate - деактивация пользователя"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    # Проверяем права администратора
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    # Получаем аргументы команды
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "🚫 <b>Деактивация пользователя</b>\n\n"
            "Использование: <code>/deactivate ID_пользователя</code>\n\n"
            "Пример: <code>/deactivate 123456789</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        # Извлекаем ID пользователя
        target_user_id = int(context.args[0])
        target_username = get_username_by_id(target_user_id)
        
        # Проверяем, не пытаемся ли деактивировать админа
        if is_admin(target_user_id):
            await update.message.reply_text(
                "❌ <b>Нельзя деактивировать администратора</b>\n\n"
                "Администраторы не могут быть деактивированы.",
                parse_mode='HTML'
            )
            return
        
        # Проверяем текущий статус
        current_status = is_user_active(target_user_id)
        
        if not current_status:
            await update.message.reply_text(
                f"ℹ️ <b>Пользователь уже неактивен</b>\n\n"
                f"👤 <b>Пользователь:</b> @{target_username} (ID: {target_user_id})\n"
                f"🚫 <b>Статус:</b> Неактивен",
                parse_mode='HTML'
            )
            return
        
        # Деактивируем пользователя
        success = deactivate_user(target_user_id)
        
        if success:
            # Логируем действие
            log_message(user_id, target_user_id, username, target_username, 'admin_action', 'user_deactivated')
            
            await update.message.reply_text(
                f"🚫 <b>Пользователь деактивирован!</b>\n\n"
                f"👤 <b>Пользователь:</b> @{target_username} (ID: {target_user_id})\n"
                f"🔄 <b>Статус:</b> Активен → Неактивен",
                parse_mode='HTML'
            )
            
            logger.info(f"🚫 Админ {username} (ID: {user_id}) деактивировал пользователя {target_username} (ID: {target_user_id})")
        else:
            await update.message.reply_text(
                f"❌ <b>Ошибка деактивации пользователя</b>\n\n"
                f"Пользователь с ID {target_user_id} не найден или произошла ошибка.",
                parse_mode='HTML'
            )
        
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка в ID пользователя</b>\n\n"
            "ID должен быть числом.\n"
            "Пример: <code>/deactivate 123456789</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка деактивации пользователя</b>\n\n"
            f"Ошибка: {str(e)}"
        )
        logger.error(f"❌ Ошибка деактивации пользователя админом {username}: {e}")
