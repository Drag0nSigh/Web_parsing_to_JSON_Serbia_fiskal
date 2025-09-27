"""
Декоратор для измерения времени выполнения функций
"""
import time
import functools
import logging
from typing import Callable, Any

# Настройка логгера
from utils.log_manager import get_log_manager

# Получаем менеджер логов
log_manager = get_log_manager()

# Настраиваем логирование
logger = log_manager.setup_logging("timing", logging.INFO)


def timing_decorator(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения функции
    
    Args:
        func: Функция для обертывания
        
    Returns:
        Обернутая функция с измерением времени
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Форматируем время
            if execution_time < 1:
                time_str = f"{execution_time * 1000:.2f}ms"
            else:
                time_str = f"{execution_time:.2f}s"
            
            logger.info(f"⏱️  {func.__name__}() выполнилась за {time_str}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Форматируем время
            if execution_time < 1:
                time_str = f"{execution_time * 1000:.2f}ms"
            else:
                time_str = f"{execution_time:.2f}s"
            
            logger.error(f"❌ {func.__name__}() завершилась с ошибкой за {time_str}: {e}")
            raise
    
    return wrapper


def async_timing_decorator(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения асинхронной функции
    
    Args:
        func: Асинхронная функция для обертывания
        
    Returns:
        Обернутая асинхронная функция с измерением времени
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Форматируем время
            if execution_time < 1:
                time_str = f"{execution_time * 1000:.2f}ms"
            else:
                time_str = f"{execution_time:.2f}s"
            
            logger.info(f"⏱️  {func.__name__}() выполнилась за {time_str}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Форматируем время
            if execution_time < 1:
                time_str = f"{execution_time * 1000:.2f}ms"
            else:
                time_str = f"{execution_time:.2f}s"
            
            logger.error(f"❌ {func.__name__}() завершилась с ошибкой за {time_str}: {e}")
            raise
    
    return wrapper
