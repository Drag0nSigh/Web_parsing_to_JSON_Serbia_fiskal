"""
Менеджер логирования с ежедневными файлами и автоудалением старых логов
"""
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import glob


class LogManager:
    """Менеджер для управления логами с ежедневными файлами"""
    
    def __init__(self, log_dir: Path, retention_days: int = 30):
        """
        Инициализация менеджера логов
        
        Args:
            log_dir: Папка для хранения логов
            retention_days: Количество дней хранения логов
        """
        self.log_dir = log_dir
        self.retention_days = retention_days
        self.log_dir.mkdir(exist_ok=True)
        
        # Очищаем старые логи при инициализации
        self.cleanup_old_logs()
    
    def get_daily_log_file(self, log_type: str = "bot") -> Path:
        """
        Получить путь к файлу лога для текущего дня
        
        Args:
            log_type: Тип лога (bot, parser, requests, etc.)
            
        Returns:
            Path к файлу лога
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{log_type}_{today}.log"
        return self.log_dir / filename
    
    def setup_logging(self, log_type: str = "bot", level: int = logging.INFO) -> logging.Logger:
        """
        Настроить логирование для указанного типа
        
        Args:
            log_type: Тип лога
            level: Уровень логирования
            
        Returns:
            Настроенный логгер
        """
        # Получаем путь к файлу лога
        log_file = self.get_daily_log_file(log_type)
        
        # Создаем логгер
        logger = logging.getLogger(log_type)
        logger.setLevel(level)
        
        # Очищаем существующие обработчики
        logger.handlers.clear()
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Обработчик для файла
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Отключаем распространение на корневой логгер
        logger.propagate = False
        
        return logger
    
    def cleanup_old_logs(self) -> int:
        """
        Удалить старые файлы логов
        
        Returns:
            Количество удаленных файлов
        """
        if not self.log_dir.exists():
            return 0
        
        # Вычисляем дату, до которой удаляем файлы
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_count = 0
        
        # Ищем все файлы логов
        log_pattern = str(self.log_dir / "*.log")
        log_files = glob.glob(log_pattern)
        
        for log_file in log_files:
            try:
                # Получаем дату создания файла
                file_time = datetime.fromtimestamp(os.path.getctime(log_file))
                
                # Если файл старше cutoff_date, удаляем его
                if file_time < cutoff_date:
                    os.remove(log_file)
                    deleted_count += 1
                    
            except (OSError, ValueError) as e:
                # Игнорируем ошибки при удалении файлов
                continue
        
        return deleted_count
    
    def get_log_files(self, log_type: Optional[str] = None) -> list[Path]:
        """
        Получить список файлов логов
        
        Args:
            log_type: Тип лога (если None, возвращает все)
            
        Returns:
            Список путей к файлам логов
        """
        if not self.log_dir.exists():
            return []
        
        if log_type:
            pattern = f"{log_type}_*.log"
        else:
            pattern = "*.log"
        
        log_pattern = str(self.log_dir / pattern)
        return [Path(f) for f in glob.glob(log_pattern)]
    
    def get_log_stats(self) -> dict:
        """
        Получить статистику по логам
        
        Returns:
            Словарь со статистикой
        """
        log_files = self.get_log_files()
        
        total_files = len(log_files)
        total_size = sum(f.stat().st_size for f in log_files if f.exists())
        
        # Группируем по типам
        types = {}
        for log_file in log_files:
            # Извлекаем тип из имени файла (например, bot_2025-09-27.log -> bot)
            type_name = log_file.stem.split('_')[0]
            if type_name not in types:
                types[type_name] = {'count': 0, 'size': 0}
            types[type_name]['count'] += 1
            types[type_name]['size'] += log_file.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'retention_days': self.retention_days,
            'types': types
        }


def get_log_manager() -> LogManager:
    """
    Получить экземпляр менеджера логов с настройками из окружения
    
    Returns:
        Настроенный LogManager
    """
    import os
    from pathlib import Path
    
    # Определяем путь к логам в зависимости от окружения
    if os.getenv("DOCKER_ENV") or (os.path.exists("/app") and os.path.exists("/app/bot_tg")):
        log_dir = Path("/app/log")
    else:
        # Определяем путь относительно текущего файла
        current_dir = Path(__file__).parent.parent  # src/
        log_dir = current_dir / "log"
    
    # Получаем количество дней хранения из переменной окружения
    retention_days = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    
    return LogManager(log_dir, retention_days)
