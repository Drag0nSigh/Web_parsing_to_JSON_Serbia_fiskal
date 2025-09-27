"""
Команды для обычных пользователей
"""
import json
import re
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from parser.fiscal_parser import parse_serbian_fiscal_url
from db.utils import log_user_request, check_daily_limit, log_user_request, is_user_active, has_sent_blocked_message, log_message
from .admin_commands import is_admin

# Настройка логирования
logger = logging.getLogger(__name__)

# ID администратора
admin_id = int(os.getenv('ADMIN_ID', '0'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    # Проверяем, активен ли пользователь
    if not is_user_active(user_id):
        # Проверяем, отправлял ли уже сообщение после блокировки
        if has_sent_blocked_message(user_id):
            await update.message.reply_text(
                "🚫 <b>Ваш аккаунт заблокирован</b>\n\n"
                "❌ Вы уже отправили сообщение администратору.\n"
                "📞 Ожидайте ответа от администратора.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "🚫 <b>Ваш аккаунт заблокирован</b>\n\n"
                "❌ Парсинг ссылок недоступен.\n"
                "📞 У вас есть возможность отправить <b>одно сообщение</b> администратору.\n\n"
                "💬 Используйте команду: <code>/admin ваш текст сообщения</code>",
                parse_mode='HTML'
            )
        return
    
    # Проверяем, является ли пользователь администратором
    if is_admin(user_id):
        from .telegram_bot import create_admin_menu
        await update.message.reply_text(
            "🤖 <b>Добро пожаловать в бот для парсинга фискальных данных!</b>\n\n"
            "📋 Отправьте мне ссылку на сербский фискальный чек, и я верну JSON в российском формате.\n\n"
            "🔗 Бот принимает только ссылки!\n\n"
            "💡 <b>Пример ссылки:</b>\n"
            "https://suf.purs.gov.rs/v/?vl=...",
            parse_mode='HTML',
            reply_markup=create_admin_menu()
        )
    else:
        help_text = """
🤖 <b>Добро пожаловать в бот для парсинга фискальных данных!</b>

📋 <b>Как использовать:</b>
1. Отправьте ссылку на сербский фискальный чек
2. Бот автоматически обработает ссылку
3. Получите JSON в российском формате

🔗 <b>Бот принимает только ссылки!</b>

💡 <b>Пример ссылки:</b>
https://suf.purs.gov.rs/v/?vl=...

⚠️ <b>Ограничения:</b>
• Максимум 20 ссылок в день на пользователя
• Лимит сбрасывается каждый день в 00:00
• В JSON ответе указано количество использованных запросов (X/20)

📞 <b>Нужна помощь?</b>
Используйте команду /help для получения справки
Используйте команду /admin для связи с администратором

❓ <b>Проблемы?</b>
Если бот не отвечает или выдает ошибку, попробуйте:
• Проверить правильность ссылки
• Отправить ссылку еще раз
• Обратиться к администратору
        """
        await update.message.reply_text(help_text, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    
    help_text = """
🤖 <b>Помощь по использованию бота</b>

📋 <b>Как использовать:</b>
1. Отправьте ссылку на сербский фискальный чек
2. Бот автоматически обработает ссылку
3. Получите JSON в российском формате

🔗 <b>Бот принимает только ссылки!</b>

💡 <b>Пример ссылки:</b>
https://suf.purs.gov.rs/v/?vl=...

⚠️ <b>Ограничения:</b>
• Максимум 20 ссылок в день на пользователя
• Лимит сбрасывается каждый день в 00:00
• В JSON ответе указано количество использованных запросов (X/20)

📞 <b>Команды:</b>
• <code>/start</code> - начать работу с ботом
• <code>/help</code> - показать эту справку
• <code>/admin текст сообщения</code> - отправить сообщение администратору

❓ <b>Проблемы?</b>
Если бот не отвечает или выдает ошибку, попробуйте:
• Проверить правильность ссылки
• Отправить ссылку еще раз
• Обратиться к администратору командой /admin
    """
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin - отправка сообщения администратору"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"

    # Проверяем, активен ли пользователь
    if not is_user_active(user_id):
        # Если пользователь заблокирован, проверяем, отправлял ли уже сообщение
        if has_sent_blocked_message(user_id):
            await update.message.reply_text(
                "🚫 <b>Сообщение уже отправлено</b>\n\n"
                "❌ Вы уже отправили сообщение администратору после блокировки.\n"
                "📞 Ожидайте ответа от администратора.",
                parse_mode='HTML'
            )
            return
        # Если не отправлял, разрешаем отправить одно сообщение
    else:
        # Если пользователь активен, проверяем дневной лимит
        limit_info = check_daily_limit(user_id)
        if not limit_info['can_make_request']:
            await update.message.reply_text(
                f"⚠️ <b>Дневной лимит исчерпан!</b>\n\n"
                f"📊 <b>Использовано запросов:</b> {limit_info['current_count']}/{limit_info['limit']}\n\n"
                f"⏰ <b>Лимит сбросится:</b> завтра в 00:00\n\n"
                f"💡 <b>Попробуйте завтра или обратитесь к администратору</b>",
                parse_mode='HTML'
            )
            return

    # Получаем текст сообщения после команды
    if context.args:
        message_text = ' '.join(context.args)
        
        # Отправляем сообщение администратору
        try:
            
            # Определяем тип сообщения
            is_blocked = not is_user_active(user_id)
            message_type = 'blocked_user_message' if is_blocked else 'user_message'
            
            admin_message_text = f"""
📨 <b>Сообщение от пользователя</b>

👤 <b>Пользователь:</b> @{username} (ID: {user_id})
📝 <b>Сообщение:</b> {message_text}
{'🚫 <b>Статус:</b> Заблокирован' if is_blocked else '✅ <b>Статус:</b> Активен'}

⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message_text,
                parse_mode='HTML'
            )
            
            # Логируем сообщение
            log_message(user_id, admin_id, username, 'admin', 'user_to_admin', message_type)
            
            # Если пользователь заблокирован, сообщаем что это последнее сообщение
            if is_blocked:
                await update.message.reply_text(
                    "✅ <b>Сообщение отправлено администратору!</b>\n\n"
                    "🚫 Это ваше единственное сообщение после блокировки.\n"
                    "📞 Ожидайте ответа от администратора.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "✅ <b>Сообщение отправлено администратору!</b>\n\n"
                    "Спасибо за обращение. Администратор ответит вам в ближайшее время.",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            from .telegram_bot import logger
            logger.error(f"❌ Ошибка отправки сообщения администратору: {e}")
            await update.message.reply_text(
                "❌ <b>Ошибка отправки сообщения</b>\n\n"
                "Не удалось отправить сообщение администратору. Попробуйте позже.",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "📨 <b>Отправка сообщения администратору</b>\n\n"
            "Использование: <code>/admin ваш текст сообщения</code>\n\n"
            "💡 <b>Пример:</b>\n"
            "<code>/admin У меня проблема с парсингом ссылки</code>",
            parse_mode='HTML'
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех сообщений"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без_username"
    message_text = update.message.text.strip()
    
    # Проверяем, активен ли пользователь
    if not is_user_active(user_id):
        await update.message.reply_text(
            "🚫 <b>Ваш аккаунт заблокирован</b>\n\n"
            "❌ Парсинг ссылок недоступен.\n"
            "📞 У вас есть возможность отправить <b>одно сообщение</b> администратору.\n\n"
            "💬 Используйте команду: <code>/admin ваш текст сообщения</code>",
            parse_mode='HTML'
        )
        return
    
    # Проверяем, является ли сообщение URL
    if not is_url(message_text):
        await update.message.reply_text(
            "❌ Сообщение не является ссылкой!\n\n"
            "🔗 Бот принимает только ссылки на сербские фискальные чеки."
        )
        return
    
    # Проверяем дневной лимит запросов
    limit_info = check_daily_limit(user_id)
    if not limit_info['can_make_request']:
        await update.message.reply_text(
            f"⚠️ <b>Дневной лимит исчерпан!</b>\n\n"
            f"📊 <b>Использовано запросов:</b> {limit_info['current_count']}/{limit_info['limit']}\n\n"
            f"⏰ <b>Лимит сбросится:</b> завтра в 00:00\n\n"
            f"💡 <b>Попробуйте завтра или обратитесь к администратору</b>",
            parse_mode='HTML'
        )
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "⏳ Обрабатываю ссылку...\n"
        "🔄 Парсинг может занять некоторое время..."
    )
    
    try:
        # Парсим URL с созданием нового драйвера при каждом запросе
        from .telegram_bot import logger
        logger.info(f"Парсинг URL: {message_text}")
        result = parse_serbian_fiscal_url(message_text, headless=True)
        
        # Записываем в лог
        log_user_request(
            user_id=user_id, 
            username=username, 
            status='success'
        )
        
        # Получаем обновленную информацию о лимите
        updated_limit_info = check_daily_limit(user_id)
        
        # Добавляем информацию о лимите в JSON
        # Результат всегда должен быть списком, как ожидает программа
        if isinstance(result, list):
            # result уже список - используем его
            result_with_limit = result.copy()
            # Добавляем мета-информацию в первый элемент списка
            if result_with_limit and isinstance(result_with_limit[0], dict):
                result_with_limit[0]['daily_requests'] = f"{updated_limit_info['current_count']}/{updated_limit_info['limit']}"
                result_with_limit[0]['remaining_requests'] = updated_limit_info['remaining']
        else:
            # Если result - это dict, оборачиваем в список
            result_item = result.copy() if isinstance(result, dict) else result
            if isinstance(result_item, dict):
                result_item['daily_requests'] = f"{updated_limit_info['current_count']}/{updated_limit_info['limit']}"
                result_item['remaining_requests'] = updated_limit_info['remaining']
            result_with_limit = [result_item]
        
        # Отправляем результат
        await processing_msg.edit_text(
            "✅ Парсинг завершен!\n\n"
            "📄 Отправляю JSON файл..."
        )
        
        # Отправляем JSON как файл
        json_text = json.dumps(result_with_limit, ensure_ascii=False, indent=2)
        
        await update.message.reply_document(
            document=json_text.encode('utf-8'),
            filename=f"fiscal_data_{datetime.now().strftime('%d%m%y_%H-%M-%S')}.json",
            caption=f"📄 JSON данные в российском формате\n\n📊 Запросов сегодня: {updated_limit_info['current_count']}/{updated_limit_info['limit']}"
        )
        
    except Exception as e:
        from .telegram_bot import logger
        logger.error(f"Ошибка при парсинге: {e}")
        
        # Логируем ошибку
        log_user_request(
            user_id=user_id,
            username=username,
            status='error'
        )
        
        await processing_msg.edit_text(
            f"❌ <b>Ошибка при обработке ссылки:</b>\n\n"
            f"🔍 {str(e)}\n\n"
            "Попробуйте другую ссылку или обратитесь к администратору.",
            parse_mode='HTML'
        )


def is_url(text: str) -> bool:
    """Проверяет, является ли текст URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(text) is not None
