import os
import json
import keyboard
import win32api
import logging

from utils_path import get_app_dir

logger = logging.getLogger("lithoscan-hud")

# ЖЕСТКИЙ ОТКАТНЫЙ ВАРИАНТ (ЕСЛИ ФАЙЛ БУДЕТ ПОЛНОСТЬЮ УДАЛЕН)
FALLBACK_BINDINGS = {
    "toggle_mode": "alt+g",
    "visibility": "alt+v",
    "snapshot": "alt+ctrl",
    "point1_main": "alt+1",
    "point2_main": "alt+2",
    "scan_main": "alt+x",
    "point1_sig": "alt+3",
    "point2_sig": "alt+4",
    "scan_sig": "f3"
}

# ШАБЛОН ДЛЯ АВТОМАТИЧЕСКОЙ ГЕНЕРАЦИИ ИНСТРУКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЯ
DEFAULT_HOTKEYS_JSON = {
    "_instructions": [
        "INSTRUCTIONS:",
        "1. Write hotkeys in LOWERCASE and WITHOUT spaces (e.g., 'alt+x', 'f3', 'alt+ctrl').",
        "2. Available modifiers: 'alt', 'ctrl', 'shift', 'win'.",
        "3. Hotkeys reload dynamically when you click the circular arrow in the Settings."
    ],
    "keybindings": {
        "toggle_mode": "alt+g",
        "visibility": "alt+v",
        "snapshot": "alt+ctrl",
        "point1_main": "alt+1",
        "point2_main": "alt+2",
        "scan_main": "alt+x",
        "point1_sig": "alt+3",
        "point2_sig": "alt+4",
        "scan_sig": "f3"
    },
    "_descriptions": {
        "toggle_mode": "Toggle setup mode (unlock click-through)",
        "visibility": "Show/Hide the entire overlay",
        "snapshot": "Save a debug snapshot of the last scan",
        "point1_main": "Set Point 1 for the Asteroid Scan Area",
        "point2_main": "Set Point 2 for the Asteroid Scan Area",
        "scan_main": "Start scanning the asteroid",
        "point1_sig": "Set Point 1 for the Signature Decoder Area",
        "point2_sig": "Set Point 2 for the Signature Decoder Area",
        "scan_sig": "Start decoding the radar signature"
    }
}

class InputHandler:
    def __init__(self, controller):
        self.controller = controller
        self.p1_main = None
        self.p1_sig = None
        
        data_dir = os.path.join(get_app_dir(), "data")
        self.hotkeys_file = os.path.join(data_dir, "hotkeys.json")

    # --- ЧТЕНИЕ КОНФИГУРАЦИИ ---
    def _load_hotkeys(self) -> dict:
        """Безопасно загружает хоткеи из структурированного JSON или создает новый"""
        if os.path.exists(self.hotkeys_file):
            try:
                with open(self.hotkeys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_bindings = data.get("keybindings", {})
                    
                    # Склеиваем с дефолтами на случай, если пользователь удалил какую-то строку
                    merged = FALLBACK_BINDINGS.copy()
                    
                    for key, val in user_bindings.items():
                        if key in merged and isinstance(val, str):
                            # УМНАЯ ОЧИСТКА: убираем пробелы, переводим в нижний регистр
                            cleaned_val = val.strip().lower().replace(" ", "")
                            merged[key] = cleaned_val
                            
                    return merged
            except Exception as e:
                logger.error(f"[ERROR] Ошибка чтения hotkeys.json: {e}. Откат на дефолты.")
                return FALLBACK_BINDINGS
        else:
            # Создаем красивый документированный файл по умолчанию
            try:
                os.makedirs(os.path.dirname(self.hotkeys_file), exist_ok=True)
                with open(self.hotkeys_file, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_HOTKEYS_JSON, f, indent=4, ensure_ascii=False)
                logger.info(f"[FILES] Создан файл конфигурации хоткеев по умолчанию: {self.hotkeys_file}")
            except Exception as e:
                logger.error(f"[WARNING] Не удалось создать файл hotkeys.json: {e}")
            return FALLBACK_BINDINGS

    # --- ТРИГГЕРЫ ---
    def trigger_toggle_mode(self): self.controller.toggle_mode()
    def trigger_visibility(self): self.controller.toggle_visibility()
    def trigger_snapshot(self): self.controller.save_debug_snapshot()

    def trigger_point1_main(self):
        x, y = win32api.GetCursorPos()
        self.p1_main = (x, y)
        self.controller.set_point1(self.p1_main, is_signature=False)

    def trigger_point2_main(self):
        if not self.p1_main: return
        x, y = win32api.GetCursorPos()
        self.controller.set_region(self.p1_main, (x, y), is_signature=False)
        self.p1_main = None

    def trigger_scan_main(self): self.controller.start_scan()

    def trigger_point1_sig(self):
        x, y = win32api.GetCursorPos()
        self.p1_sig = (x, y)
        self.controller.set_point1(self.p1_sig, is_signature=True)

    def trigger_point2_sig(self):
        if not self.p1_sig: return
        x, y = win32api.GetCursorPos()
        self.controller.set_region(self.p1_sig, (x, y), is_signature=True)
        self.p1_sig = None

    def trigger_scan_sig(self): self.controller.start_signature_scan()

    # --- РЕГИСТРАЦИЯ ХОТКЕЕВ ---
    def register_hotkeys(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass

        config = self._load_hotkeys()

        try:
            # Системные клавиши
            keyboard.add_hotkey(config["toggle_mode"], self.trigger_toggle_mode)
            keyboard.add_hotkey(config["visibility"], self.trigger_visibility)
            keyboard.add_hotkey(config["snapshot"], self.trigger_snapshot)
            
            # Калькулятор астероидов
            keyboard.add_hotkey(config["point1_main"], self.trigger_point1_main)
            keyboard.add_hotkey(config["point2_main"], self.trigger_point2_main)
            keyboard.add_hotkey(config["scan_main"], self.trigger_scan_main)
            
            # Декодер сигнатур
            keyboard.add_hotkey(config["point1_sig"], self.trigger_point1_sig)
            keyboard.add_hotkey(config["point2_sig"], self.trigger_point2_sig)
            keyboard.add_hotkey(config["scan_sig"], self.trigger_scan_sig)
            
            logger.info(f"[HOTKEYS] Хоткеи зарегистрированы. Файл: {os.path.basename(self.hotkeys_file)}")
        except Exception as e:
            logger.error(f"[ERROR] Ошибка назначения хоткеев: {e}. Проверь синтаксис в hotkeys.json!")
            self._fallback_register_defaults()

    def _fallback_register_defaults(self):
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(FALLBACK_BINDINGS["toggle_mode"], self.trigger_toggle_mode)
            keyboard.add_hotkey(FALLBACK_BINDINGS["visibility"], self.trigger_visibility)
            keyboard.add_hotkey(FALLBACK_BINDINGS["snapshot"], self.trigger_snapshot)
            keyboard.add_hotkey(FALLBACK_BINDINGS["point1_main"], self.trigger_point1_main)
            keyboard.add_hotkey(FALLBACK_BINDINGS["point2_main"], self.trigger_point2_main)
            keyboard.add_hotkey(FALLBACK_BINDINGS["scan_main"], self.trigger_scan_main)
            keyboard.add_hotkey(FALLBACK_BINDINGS["point1_sig"], self.trigger_point1_sig)
            keyboard.add_hotkey(FALLBACK_BINDINGS["point2_sig"], self.trigger_point2_sig)
            keyboard.add_hotkey(FALLBACK_BINDINGS["scan_sig"], self.trigger_scan_sig)
            logger.warning("[HOTKEYS] Система успешно откатилась на дефолтные хоткеи.")
        except Exception as e:
            logger.critical(f"[HOTKEYS] Критический сбой при аварийной регистрации: {e}")