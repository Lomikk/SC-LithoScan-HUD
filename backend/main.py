import asyncio
import logging
import sys

from controller import OverlayController
from input_handler import InputHandler
from server import WebSocketServer

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("debug_log.txt", mode='a')]
)

async def main():
    # 1. Создаем контроллер (мозг)
    controller = OverlayController()
    controller.set_loop(asyncio.get_running_loop())

    # 2. Настраиваем хоткеи
    input_handler = InputHandler(controller)
    input_handler.register_hotkeys()

    # 3. Запускаем сервер
    server = WebSocketServer(controller, port=8765)
    
    print("\n" + "="*50)
    print("🚀 MINER OVERLAY БЭКЕНД УСПЕШНО ЗАПУЩЕН")
    print("="*50 + "\n")

    await server.start()

if __name__ == "__main__":
    asyncio.run(main())