import asyncio
import logging
import sys
import os

from controller import OverlayController
from input_handler import InputHandler
from server import WebSocketServer

from utils_path import get_app_dir

log_file_path = os.path.join(get_app_dir(), "debug_log.txt")
# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file_path, mode='a', encoding='utf-8')]
)

async def main():
    # 1. Создаем контроллер (мозг)
    controller = OverlayController()
    controller.set_loop(asyncio.get_running_loop())

    # 2. Настраиваем хоткеи
    input_handler = InputHandler(controller)
    input_handler.register_hotkeys()

    # ПЕРЕДАЕМ ССЫЛКУ ДЛЯ ВОЗМОЖНОСТИ ГОРЯЧЕЙ ПЕРЕЗАГРУЗКИ КНОПКОЙ ИЗ UI
    controller.set_input_handler(input_handler)

    # 3. Запускаем сервер
    server = WebSocketServer(controller, port=8765)
    
    print("\n" + "="*50)
    print("MINER OVERLAY БЭКЕНД УСПЕШНО ЗАПУЩЕН")
    print("="*50 + "\n")

    await server.start()

if __name__ == "__main__":
    asyncio.run(main())