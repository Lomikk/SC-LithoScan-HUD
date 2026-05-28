import time
import sys

# =========================================================================
# ПРОФАЙЛЕР ЗАПУСКА (Замеряем время от старта процесса)
# =========================================================================
T_START = time.perf_counter()

def t_log(step_name):
    """Выводит в консоль время, прошедшее с момента старта скрипта"""
    elapsed = time.perf_counter() - T_START
    print(f"[PROFILE] {elapsed:>5.2f}s | {step_name}", flush=True)

t_log("Старт скрипта. Начинаем импорт стандартных библиотек...")

import os
import logging
import asyncio
t_log("Стандартные библиотеки загружены.")

t_log("Начинаем импорт тяжелых модулей (OpenCV, RapidOCR, ONNX)...")
from utils_path import get_app_dir
from controller import OverlayController
from input_handler import InputHandler
from server import WebSocketServer
t_log("Все локальные и тяжелые модули успешно импортированы.")

# Обновляем путь к логу, чтобы он создавался рядом с .exe
log_file_path = os.path.join(get_app_dir(), "debug_log.txt")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file_path, mode='a', encoding='utf-8')]
)

async def main():
    t_log("Инициализация контроллера (Загрузка JSON баз данных)...")
    controller = OverlayController()
    controller.set_loop(asyncio.get_running_loop())
    t_log("Контроллер готов.")

    t_log("Регистрация глобальных хоткеев...")
    input_handler = InputHandler(controller)
    input_handler.register_hotkeys()
    controller.set_input_handler(input_handler)
    t_log("Хоткеи зарегистрированы.")

    print("\n" + "="*50)
    print("MINER OVERLAY БЭКЕНД УСПЕШНО ЗАПУЩЕН")
    print("="*50 + "\n")

    t_log("Биндим WebSocket сервер и отправляем сигнал готовности...")
    server = WebSocketServer(controller, port=8765)
    await server.start()

if __name__ == "__main__":
    t_log("Вход в асинхронный цикл main()...")
    asyncio.run(main())