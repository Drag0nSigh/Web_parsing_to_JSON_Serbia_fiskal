#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты для работы с базой данных
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .database import db_manager
from .models import MessageLog, User

logger = logging.getLogger(__name__)


def init_database() -> bool:
    """Инициализация базы данных (ожидание PostgreSQL после initdb/рестарта и создание таблиц)."""
    try:
        logger.info("🚀 Инициализация базы данных...")

        max_wait = int(os.getenv("DB_INIT_MAX_WAIT", "120"))
        interval = float(os.getenv("DB_INIT_RETRY_INTERVAL", "2"))
        deadline = time.monotonic() + max_wait

        while time.monotonic() < deadline:
            if db_manager.check_connection():
                break
            logger.warning("⏳ PostgreSQL ещё не готов (после первого старта контейнер может перезапускаться), ждём %.1f с...", interval)
            time.sleep(interval)
        else:
            logger.error("❌ Нет подключения к базе данных за %s с", max_wait)
            return False

        if db_manager.init_database():
            logger.info("✅ База данных успешно инициализирована")
            return True
        else:
            logger.error("❌ Ошибка инициализации базы данных")
            return False

    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации базы данных: {e}")
        return False


def log_user_request(user_id: int, username: str = None, status: str = "success", error_message: str = None) -> bool:
    """Логирование запроса пользователя"""
    try:
        # Добавляем лог запроса (автоматически создает/обновляет пользователя)
        log = db_manager.add_request_log(user_id=user_id, username=username, status=status, error_message=error_message)

        if log:
            logger.info(f"📝 Запрос пользователя {user_id} записан в лог")
            return True
        else:
            logger.warning(f"⚠️ Не удалось записать лог для пользователя {user_id}")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка логирования запроса: {e}")
        return False


def get_user_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Получение статистики пользователя за последние N дней"""
    try:
        date_from = datetime.now() - timedelta(days=days)

        logs = db_manager.get_request_logs(user_id=user_id, date_from=date_from)

        total_requests = len(logs)
        # Считаем успешными: success, command
        successful_requests = len([log for log in logs if log.status in ["success", "command"]])

        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики пользователя: {e}")
        return {}


def get_system_stats(days: int = 7) -> Dict[str, Any]:
    """Получение системной статистики"""
    try:
        stats = []
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i)
            daily_stats = db_manager.get_daily_stats(date)
            if daily_stats:
                stats.append(daily_stats)

        if not stats:
            return {}

        # Агрегируем статистику
        total_requests = sum([s["total_requests"] for s in stats])
        total_successful = sum([s["successful_requests"] for s in stats])

        # Получаем максимальное количество уникальных пользователей из всех дней
        total_users = max([s.get("unique_users", 0) for s in stats], default=0)

        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_requests - total_successful,
            "unique_users": total_users,
            "daily_stats": stats,
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения системной статистики: {e}")
        return {}


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение последних логов"""
    try:
        with db_manager.get_session() as session:
            from .models import RequestLog

            logs = session.query(RequestLog).order_by(RequestLog.created_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"❌ Ошибка получения последних логов: {e}")
        return []


def get_users_list(limit: int = 100) -> List[Dict[str, Any]]:
    """Получение списка пользователей"""
    try:
        with db_manager.get_session() as session:
            from .models import User

            users = session.query(User).order_by(User.created_at.desc()).limit(limit).all()
            return [user.to_dict() for user in users]
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка пользователей: {e}")
        return []


def get_request_logs(limit: int = 100, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
    """Получение логов запросов с фильтрацией по дате"""
    try:
        with db_manager.get_session() as session:
            from .models import RequestLog

            query = session.query(RequestLog)

            if date_from:
                query = query.filter(RequestLog.created_at >= date_from)

            if date_to:
                query = query.filter(RequestLog.created_at <= date_to)

            logs = query.order_by(RequestLog.created_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"❌ Ошибка получения логов запросов: {e}")
        return []


def cleanup_old_logs(days: int = 90) -> int:
    """Очистка старых логов (старше N дней)"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        with db_manager.get_session() as session:
            from .models import RequestLog

            deleted_count = session.query(RequestLog).filter(RequestLog.created_at < cutoff_date).delete()

            logger.info(f"🧹 Удалено {deleted_count} старых логов (старше {days} дней)")
            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка очистки старых логов: {e}")
        return 0


def get_database_info() -> Dict[str, Any]:
    """Получение информации о базе данных"""
    try:
        with db_manager.get_session() as session:
            from .models import RequestLog, User

            users_count = session.query(User).count()
            logs_count = session.query(RequestLog).count()

            # Последний лог
            last_log = session.query(RequestLog).order_by(RequestLog.created_at.desc()).first()

            return {
                "users_count": users_count,
                "logs_count": logs_count,
                "last_log_time": last_log.created_at.isoformat() if last_log else None,
                "connection_status": "active" if db_manager.check_connection() else "inactive",
            }

    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о БД: {e}")
        return {"connection_status": "error", "error": str(e)}


def get_user_daily_requests_count(user_id: int) -> int:
    """Получает количество запросов пользователя за сегодня"""
    try:
        from datetime import date, datetime

        from .database import db_manager

        with db_manager.get_session() as session:
            from .models import RequestLog

            # Получаем начало и конец сегодняшнего дня
            today = date.today()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())

            # Подсчитываем успешные запросы за сегодня
            count = (
                session.query(RequestLog)
                .filter(
                    RequestLog.user_id == user_id,
                    RequestLog.status == "success",
                    RequestLog.created_at >= start_of_day,
                    RequestLog.created_at <= end_of_day,
                )
                .count()
            )

            return count

    except Exception as e:
        logger.error(f"❌ Ошибка получения количества дневных запросов для пользователя {user_id}: {e}")
        return 0


def check_daily_limit(user_id: int, limit: int = None) -> dict:
    """Проверяет, не превышен ли дневной лимит запросов"""
    try:
        # Получаем лимит из переменной окружения, если не передан явно
        if limit is None:
            import os

            limit = int(os.getenv("DAILY_REQUEST_LIMIT", "50"))

        current_count = get_user_daily_requests_count(user_id)

        return {
            "can_make_request": current_count < limit,
            "current_count": current_count,
            "limit": limit,
            "remaining": max(0, limit - current_count),
        }

    except Exception as e:
        logger.error(f"❌ Ошибка проверки дневного лимита для пользователя {user_id}: {e}")
        return {
            "can_make_request": True,  # В случае ошибки разрешаем запрос
            "current_count": 0,
            "limit": limit,
            "remaining": limit,
        }


def log_message(
    sender_user_id: int,
    recipient_user_id: int,
    sender_username: str,
    recipient_username: str,
    direction: str,
    message_type: str,
) -> None:
    """Логирование сообщения между пользователем и администратором"""
    try:
        with db_manager.get_session() as session:
            message_log = MessageLog(
                sender_user_id=sender_user_id,
                recipient_user_id=recipient_user_id,
                sender_username=sender_username,
                recipient_username=recipient_username,
                direction=direction,
                message_type=message_type,
            )
            session.add(message_log)
            session.commit()
            logger.info(f"📝 Сообщение {direction} от пользователя {sender_user_id} записано в лог")
    except Exception as e:
        logger.error(f"❌ Ошибка записи сообщения в лог: {e}")


def has_sent_blocked_message(user_id: int) -> bool:
    """Проверяет, отправлял ли заблокированный пользователь сообщение администратору"""
    try:
        with db_manager.get_session() as session:
            count = (
                session.query(MessageLog)
                .filter(
                    MessageLog.sender_user_id == user_id,
                    MessageLog.direction == "user_to_admin",
                    MessageLog.message_type == "blocked_user_message",
                )
                .count()
            )
            return count > 0
    except Exception as e:
        logger.error(f"❌ Ошибка проверки отправки сообщения заблокированным пользователем {user_id}: {e}")
        return False


def get_user_message_count(user_id: int, direction: str = None) -> int:
    """Получить количество сообщений пользователя (всех или определенного направления)"""
    try:
        with db_manager.get_session() as session:
            query = session.query(MessageLog).filter(MessageLog.sender_user_id == user_id)
            if direction:
                query = query.filter(MessageLog.direction == direction)
            return query.count()
    except Exception as e:
        logger.error(f"❌ Ошибка получения количества сообщений для пользователя {user_id}: {e}")
        return 0


def is_user_active(user_id: int) -> bool:
    """Проверяет, активен ли пользователь"""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                return user.is_active
            return True  # Если пользователь не найден, считаем активным
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса пользователя {user_id}: {e}")
        return True  # В случае ошибки считаем активным


def get_username_by_id(user_id: int) -> str:
    """Получает username по id"""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            return user.username if user else f"user_{user_id}"
    except Exception as e:
        logger.error(f"❌ Ошибка получения username пользователя {user_id}: {e}")
        return f"user_{user_id}"


def set_user_active_status(user_id: int, is_active: bool) -> bool:
    """Устанавливает статус активности пользователя"""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.is_active = is_active
                user.last_activity = datetime.utcnow()
                session.commit()
                logger.info(f"✅ Статус пользователя {user_id} изменен на {'активен' if is_active else 'неактивен'}")
                return True
            else:
                logger.warning(f"⚠️ Пользователь {user_id} не найден")
                return False
    except Exception as e:
        logger.error(f"❌ Ошибка изменения статуса пользователя {user_id}: {e}")
        return False


def activate_user(user_id: int) -> bool:
    """Активирует пользователя"""
    return set_user_active_status(user_id, True)


def deactivate_user(user_id: int) -> bool:
    """Деактивирует пользователя"""
    return set_user_active_status(user_id, False)
