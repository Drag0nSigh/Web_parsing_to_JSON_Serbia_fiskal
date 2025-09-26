#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для перезапуска бота в Linux
"""

import os
import sys
import time
import signal
import subprocess
import psutil
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def find_bot_processes():
    """Найти все процессы бота"""
    bot_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('start_bot.py' in arg or 'telegram_bot.py' in arg for arg in cmdline):
                bot_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return bot_processes

def stop_bot_processes():
    """Остановить все процессы бота"""
    print("Остановка бота...")
    
    processes = find_bot_processes()
    if not processes:
        print("ИНФО: Процессы бота не найдены")
        return True
    
    # Сначала пытаемся остановить gracefully
    for proc in processes:
        try:
            print(f"Останавливаем процесс {proc.pid}")
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Ждем 3 секунды
    time.sleep(3)
    
    # Проверяем, что процессы остановились
    remaining_processes = find_bot_processes()
    if remaining_processes:
        print("ВНИМАНИЕ: Принудительная остановка процессов...")
        for proc in remaining_processes:
            try:
                print(f"Принудительно останавливаем процесс {proc.pid}")
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    # Финальная проверка
    time.sleep(1)
    final_processes = find_bot_processes()
    if final_processes:
        print(f"ОШИБКА: Не удалось остановить {len(final_processes)} процессов")
        return False
    else:
        print("УСПЕХ: Все процессы бота остановлены")
        return True

def start_bot():
    """Запустить бота"""
    print("Запуск бота...")
    
    # Получаем путь к скрипту запуска
    script_dir = Path(__file__).parent
    start_script = script_dir / "start_bot.py"
    
    if not start_script.exists():
        print(f"ОШИБКА: Файл {start_script} не найден")
        return False
    
    try:
        # Запускаем бота в фоновом режиме
        process = subprocess.Popen(
            [sys.executable, str(start_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir.parent.parent,  # Переходим в корень проекта
            text=True,  # Используем текстовый режим
            encoding='utf-8',  # Явно указываем кодировку
            errors='replace'  # Заменяем нечитаемые символы
        )
        
        print(f"УСПЕХ: Бот запущен с PID {process.pid}")
        return True
        
    except Exception as e:
        print(f"ОШИБКА: Ошибка запуска бота: {e}")
        return False

def restart_bot():
    """Перезапустить бота"""
    print("Перезапуск бота...")
    
    # Останавливаем бота
    if not stop_bot_processes():
        print("ОШИБКА: Не удалось остановить бота")
        return False
    
    # Ждем немного
    time.sleep(2)
    
    # Запускаем бота
    if not start_bot():
        print("ОШИБКА: Не удалось запустить бота")
        return False
    
    print("УСПЕХ: Бот успешно перезапущен")
    return True

def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "--restart":
        restart_bot()
    else:
        print("Использование: python restart_bot.py --restart")

if __name__ == "__main__":
    main()
