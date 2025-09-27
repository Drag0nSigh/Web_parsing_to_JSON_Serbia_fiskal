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


class MessageLog(Base):
    """Модель лога сообщений между пользователями и администратором"""
    __tablename__ = 'message_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_user_id = Column(BigInteger, nullable=False, index=True)
    recipient_user_id = Column(BigInteger, nullable=False, index=True)
    sender_username = Column(String(255), nullable=True)
    recipient_username = Column(String(255), nullable=True)
    direction = Column(String(20), nullable=False)  # 'user_to_admin' или 'admin_to_user'
    message_type = Column(String(50), nullable=False)  # 'blocked_user_message', 'admin_response', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<MessageLog(user_id={self.user_id}, direction='{self.direction}', type='{self.message_type}')>"

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'sender_user_id': self.sender_user_id,
            'recipient_user_id': self.recipient_user_id,
            'sender_username': self.username,
            'recipient_username': self.recipient_username,
            'direction': self.direction,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }