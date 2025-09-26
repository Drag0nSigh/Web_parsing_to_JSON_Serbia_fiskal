#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Административные команды для телеграм бота
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from utils.timing_decorator import async_timing_decorator
from db.utils import get_recent_logs, get_users_list, get_system_stats, get_database_info, get_request_logs

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
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID

@async_timing_decorator
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_start - приветствие для администратора"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(f"User {update.effective_user.id} is not admin, admin_id: {ADMIN_ID}")
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    admin_commands = """
🔧 <b>Административные команды:</b>

  📊 <b>Логи:</b>
  /admin_logs - все логи
  /admin_logs_26_09_25 - логи за определенную дату

👥 <b>Пользователи:</b>
/admin_users - список пользователей

🔄 <b>Управление:</b>
/admin_restart - перезапуск бота
/admin_test - тест работоспособности
/admin_status - статус системы

📈 <b>Статистика:</b>
/admin_stats - статистика использования
    """
    
    await update.message.reply_text(admin_commands, parse_mode='HTML')

@async_timing_decorator
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

@async_timing_decorator
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

@async_timing_decorator
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


@async_timing_decorator
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

@async_timing_decorator
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
        log_dir = Path("log")
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

@async_timing_decorator
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

@async_timing_decorator
async def admin_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /admin_restart - перезапуск бота"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        await update.message.reply_text("🔄 Перезапуск бота...")
        
        # Получаем путь к скрипту перезапуска
        script_dir = Path(__file__).parent
        restart_script = script_dir / "restart_bot.py"
        
        if not restart_script.exists():
            await update.message.reply_text("❌ Скрипт перезапуска не найден")
            return
        
        # Запускаем скрипт перезапуска в фоновом режиме
        import subprocess
        import sys
        
        process = subprocess.Popen(
            [sys.executable, str(restart_script), "--restart"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir.parent.parent,  # Переходим в корень проекта
            text=True,  # Используем текстовый режим
            encoding='utf-8',  # Явно указываем кодировку
            errors='replace'  # Заменяем нечитаемые символы
        )
        
        # Ждем немного для завершения перезапуска
        await asyncio.sleep(3)
        
        # Проверяем, что процесс завершился успешно
        if process.poll() is None:
            # Процесс еще работает, ждем еще
            await asyncio.sleep(2)
        
        if process.returncode == 0:
            await update.message.reply_text("✅ Бот успешно перезапущен")
        else:
            stdout, stderr = process.communicate()
            # Поскольку мы используем text=True, stderr уже строка
            error_msg = stderr if stderr else "Неизвестная ошибка"
            await update.message.reply_text(f"❌ Ошибка перезапуска: {error_msg}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при перезапуске: {str(e)}")
