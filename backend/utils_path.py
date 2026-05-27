import sys
import os

def get_app_dir():
    """Возвращает путь к рабочей папке (рядом с .exe или рядом со скриптом)"""
    if getattr(sys, 'frozen', False):
        # Если запущено как скомпилированный .exe
        return os.path.dirname(sys.executable)
    else:
        # Если запущено как обычный .py скрипт
        return os.path.dirname(os.path.abspath(__file__))