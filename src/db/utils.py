#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты для работы с базой данных
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .database import db_manager

logger = logging.getLogger(__name__)


def init_database() -> bool:
    """Инициализация базы данных"""
    try:
        logger.info("🚀 Инициализация базы данных...")
        
        # Проверяем подключение
        if not db_manager.check_connection():
            logger.error("❌ Нет подключения к базе данных")
            return False
        
        # Инициализируем базу данных
        if db_manager.init_database():
            logger.info("✅ База данных успешно инициализирована")
            return True
        else:
            logger.error("❌ Ошибка инициализации базы данных")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации базы данных: {e}")
        return False


def log_user_request(user_id: int, username: str = None, status: str = 'success', 
                    error_message: str = None) -> bool:
    """Логирование запроса пользователя"""
    try:
        # Добавляем лог запроса (автоматически создает/обновляет пользователя)
        log = db_manager.add_request_log(
            user_id=user_id,
            username=username,
            status=status,
            error_message=error_message
        )
        
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
        
        logs = db_manager.get_request_logs(
            user_id=user_id,
            date_from=date_from
        )
        
        total_requests = len(logs)
        successful_requests = len([log for log in logs if log.status == 'success'])
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': total_requests - successful_requests
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
        total_requests = sum([s['total_requests'] for s in stats])
        total_successful = sum([s['successful_requests'] for s in stats])
        total_users = len(set([s.get('unique_users', 0) for s in stats]))
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'successful_requests': total_successful,
            'failed_requests': total_requests - total_successful,
            'unique_users': total_users,
            'daily_stats': stats
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения системной статистики: {e}")
        return {}


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение последних логов"""
    try:
        logs = db_manager.get_request_logs(limit=limit)
        return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"❌ Ошибка получения последних логов: {e}")
        return []


def get_users_list(limit: int = 100) -> List[Dict[str, Any]]:
    """Получение списка пользователей"""
    try:
        users = db_manager.get_all_users(limit=limit)
        return [user.to_dict() for user in users]
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка пользователей: {e}")
        return []


def cleanup_old_logs(days: int = 90) -> int:
    """Очистка старых логов (старше N дней)"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with db_manager.get_session() as session:
            from .models import RequestLog
            deleted_count = session.query(RequestLog).filter(
                RequestLog.created_at < cutoff_date
            ).delete()
            
            logger.info(f"🧹 Удалено {deleted_count} старых логов (старше {days} дней)")
            return deleted_count
            
    except Exception as e:
        logger.error(f"❌ Ошибка очистки старых логов: {e}")
        return 0


def get_database_info() -> Dict[str, Any]:
    """Получение информации о базе данных"""
    try:
        with db_manager.get_session() as session:
            from .models import User, RequestLog
            
            users_count = session.query(User).count()
            logs_count = session.query(RequestLog).count()
            
            # Последний лог
            last_log = session.query(RequestLog).order_by(RequestLog.created_at.desc()).first()
            
            return {
                'users_count': users_count,
                'logs_count': logs_count,
                'last_log_time': last_log.created_at.isoformat() if last_log else None,
                'connection_status': 'active' if db_manager.check_connection() else 'inactive'
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о БД: {e}")
        return {'connection_status': 'error', 'error': str(e)}
