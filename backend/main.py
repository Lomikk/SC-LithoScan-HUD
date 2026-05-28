import sys
import os
import logging
import asyncio

from utils_path import get_app_dir
from controller import OverlayController
from input_handler import InputHandler
from server import WebSocketServer

# Обновляем путь к логу, чтобы он создавался рядом с .exe
log_file_path = os.path.join(get_app_dir(), "debug_log.txt")

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

    print("\n" + "="*50)
    print("MINER OVERLAY БЭКЕНД УСПЕШНО ЗАПУЩЕН")
    print("="*50 + "\n")

    # 3. Запускаем сервер
    server = WebSocketServer(controller, port=8765)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())