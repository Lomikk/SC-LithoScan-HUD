import keyboard
import win32api
import logging

logger = logging.getLogger("MinerCalc")

class InputHandler:
    def __init__(self, controller):
        self.controller = controller
        self.p1_main = None
        self.p1_sig = None

    def trigger_toggle_mode(self):
        self.controller.toggle_mode()

    # --- ХОТКЕИ ДЛЯ ГЛАВНОГО СКАНЕРА (АСТЕРОИДЫ) ---
    def trigger_point1_main(self):
        x, y = win32api.GetCursorPos()
        self.p1_main = (x, y)
        self.controller.set_point1(self.p1_main, is_signature=False)

    def trigger_point2_main(self):
        if not self.p1_main: return
        x, y = win32api.GetCursorPos()
        self.controller.set_region(self.p1_main, (x, y), is_signature=False)
        self.p1_main = None

    def trigger_scan_main(self):
        self.controller.start_scan()

    # --- ХОТКЕИ ДЛЯ СКАНЕРА СИГНАТУР ---
    def trigger_point1_sig(self):
        x, y = win32api.GetCursorPos()
        self.p1_sig = (x, y)
        self.controller.set_point1(self.p1_sig, is_signature=True)

    def trigger_point2_sig(self):
        if not self.p1_sig: return
        x, y = win32api.GetCursorPos()
        self.controller.set_region(self.p1_sig, (x, y), is_signature=True)
        self.p1_sig = None

    def trigger_scan_sig(self):
        self.controller.start_signature_scan()

    def trigger_snapshot(self):
        self.controller.save_debug_snapshot()

    def trigger_visibility(self):
        self.controller.toggle_visibility()

    def register_hotkeys(self):
        keyboard.add_hotkey('alt+g', self.trigger_toggle_mode)
        keyboard.add_hotkey('alt+v', self.trigger_visibility)
        keyboard.add_hotkey('alt+ctrl', self.trigger_snapshot)
        
        # Область и скан астероидов
        keyboard.add_hotkey('alt+1', self.trigger_point1_main)
        keyboard.add_hotkey('alt+2', self.trigger_point2_main)
        keyboard.add_hotkey('alt+x', self.trigger_scan_main)
        
        # Область и скан сигнатур
        keyboard.add_hotkey('alt+3', self.trigger_point1_sig)
        keyboard.add_hotkey('alt+4', self.trigger_point2_sig)
        keyboard.add_hotkey('alt+c', self.trigger_scan_sig)
        
        logger.info("[HOTKEYS] Хоткеи успешно зарегистрированы")