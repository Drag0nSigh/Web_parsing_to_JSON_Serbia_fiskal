#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер базы данных PostgreSQL с SQLAlchemy
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, func, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

from .models import Base, User, RequestLog

# Загружаем переменные окружения
load_dotenv()

from utils.log_manager import get_log_manager

# Получаем менеджер логов
log_manager = get_log_manager()

# Настраиваем логирование
logger = log_manager.setup_logging("database", logging.INFO)


class DatabaseManager:
    """Менеджер базы данных PostgreSQL"""
    
    def __init__(self):
        """Инициализация менеджера базы данных"""
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Настройка подключения к базе данных"""
        try:
            # Получаем параметры подключения из переменных окружения
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                # Собираем URL из отдельных параметров
                host = os.getenv('POSTGRES_HOST', 'localhost')
                port = os.getenv('POSTGRES_PORT', '5432')
                user = os.getenv('POSTGRES_USER', 'fiscal_user')
                password = os.getenv('POSTGRES_PASSWORD', 'secure_password_123')
                database = os.getenv('POSTGRES_DB', 'fiscal_data')
                
                db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            logger.info(f"Подключение к базе данных: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
            
            # Создаем движок
            self.engine = create_engine(
                db_url,
                echo=False,  # Устанавливаем True для отладки SQL запросов
                pool_pre_ping=True,  # Проверяем соединение перед использованием
                pool_recycle=3600,   # Переиспользуем соединения каждый час
            )
            
            # Создаем фабрику сессий
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info("✅ Подключение к базе данных установлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            raise
    
    def init_database(self) -> bool:
        """Инициализация базы данных (создание таблиц и схемы)"""
        try:
            logger.info("🔧 Инициализация базы данных...")
            
            # Создаем таблицы (SQLAlchemy автоматически создаст схему если нужно)
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Таблицы созданы/обновлены")
            
            logger.info("✅ База данных успешно инициализирована")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            return False
    
    
    @contextmanager
    def get_session(self):
        """Контекстный менеджер для работы с сессией"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка в сессии базы данных: {e}")
            raise
        finally:
            session.close()
    
    def check_connection(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            with self.engine.connect() as conn:
                # Простой SQL запрос для проверки подключения
                conn.execute(text("SELECT 1"))
            logger.info("✅ Подключение к базе данных работает")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            return False
    
    # Методы для работы с пользователями
    
    def create_or_update_user(self, telegram_id: int, username: str = None) -> Optional[User]:
        """Создание или обновление пользователя"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Обновляем существующего пользователя
                    user.username = username
                    user.last_activity = datetime.utcnow()
                    logger.info(f"👤 Пользователь {telegram_id} обновлен")
                else:
                    # Создаем нового пользователя
                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                    )
                    session.add(user)
                    logger.info(f"👤 Пользователь {telegram_id} создан")
                
                return user
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания/обновления пользователя: {e}")
            return None
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        try:
            with self.get_session() as session:
                return session.query(User).filter(User.telegram_id == telegram_id).first()
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя: {e}")
            return None
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Получение всех пользователей"""
        try:
            with self.get_session() as session:
                return session.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователей: {e}")
            return []
    
    def get_users_count(self) -> int:
        """Получение количества пользователей"""
        try:
            with self.get_session() as session:
                return session.query(User).count()
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета пользователей: {e}")
            return 0
    
    # Методы для работы с логами запросов
    
    def add_request_log(self, user_id: int, username: str = None, status: str = 'success', 
                       error_message: str = None) -> Optional[RequestLog]:
        """Добавление лога запроса"""
        try:
            with self.get_session() as session:
                # Сначала обновляем активность пользователя
                user = session.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    user.last_activity = datetime.utcnow()
                    if username:
                        user.username = username
                else:
                    # Создаем нового пользователя если его нет
                    user = User(
                        telegram_id=user_id,
                        username=username
                    )
                    session.add(user)
                
                # Добавляем лог запроса
                log = RequestLog(
                    user_id=user_id,
                    username=username,
                    status=status,
                    error_message=error_message
                )
                session.add(log)
                logger.info(f"📝 Лог запроса добавлен для пользователя {user_id}")
                return log
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления лога запроса: {e}")
            return None
    
    def get_request_logs(self, limit: int = 100, offset: int = 0, 
                        user_id: int = None, date_from: datetime = None,
                        date_to: datetime = None) -> List[RequestLog]:
        """Получение логов запросов с фильтрацией"""
        try:
            with self.get_session() as session:
                query = session.query(RequestLog)
                
                if user_id:
                    query = query.filter(RequestLog.user_id == user_id)
                
                if date_from:
                    query = query.filter(RequestLog.created_at >= date_from)
                
                if date_to:
                    query = query.filter(RequestLog.created_at <= date_to)
                
                return query.order_by(RequestLog.created_at.desc()).offset(offset).limit(limit).all()
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения логов запросов: {e}")
            return []
    
    def get_request_logs_count(self, user_id: int = None, date_from: datetime = None,
                              date_to: datetime = None) -> int:
        """Получение количества логов запросов"""
        try:
            with self.get_session() as session:
                query = session.query(RequestLog)
                
                if user_id:
                    query = query.filter(RequestLog.user_id == user_id)
                
                if date_from:
                    query = query.filter(RequestLog.created_at >= date_from)
                
                if date_to:
                    query = query.filter(RequestLog.created_at <= date_to)
                
                return query.count()
                
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета логов запросов: {e}")
            return 0
    
    def get_daily_stats(self, date: datetime = None) -> Dict[str, Any]:
        """Получение статистики за день"""
        try:
            if not date:
                date = datetime.now().date()
            
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            
            with self.get_session() as session:
                # Общее количество запросов
                total_requests = session.query(RequestLog).filter(
                    RequestLog.created_at >= date_start,
                    RequestLog.created_at <= date_end
                ).count()
                
                # Успешные запросы (success, command)
                successful_requests = session.query(RequestLog).filter(
                    RequestLog.created_at >= date_start,
                    RequestLog.created_at <= date_end,
                    RequestLog.status.in_(['success', 'command'])
                ).count()
                
                # Уникальные пользователи
                unique_users = session.query(RequestLog.user_id).filter(
                    RequestLog.created_at >= date_start,
                    RequestLog.created_at <= date_end
                ).distinct().count()
                
                return {
                    'date': date.isoformat(),
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': total_requests - successful_requests,
                    'unique_users': unique_users
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Соединение с базой данных закрыто")


# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
