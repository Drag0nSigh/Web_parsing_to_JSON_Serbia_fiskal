#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLAlchemy модели для базы данных
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Numeric, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }


class RequestLog(Base):
    """Модель лога запроса"""
    __tablename__ = 'request_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    status = Column(String(50), default='success', nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<RequestLog(user_id={self.user_id}, status='{self.status}', created_at='{self.created_at}')>"

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
