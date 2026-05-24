import keyboard
import win32api
import logging

logger = logging.getLogger("MinerCalc")

class InputHandler:
    def __init__(self, controller):
        self.controller = controller
        self.p1 = None

    def trigger_toggle_mode(self):
        self.controller.toggle_mode()

    def trigger_point1(self):
        x, y = win32api.GetCursorPos()
        self.p1 = (x, y)
        self.controller.set_point1(self.p1)

    def trigger_point2(self):
        if not self.p1: return
        x, y = win32api.GetCursorPos()
        self.controller.set_region(self.p1, (x, y))
        self.p1 = None

    def trigger_scan(self):
        self.controller.start_scan()

    def trigger_visibility(self):
        self.controller.toggle_visibility()

    def trigger_snapshot(self):
        self.controller.save_debug_snapshot()        

    def register_hotkeys(self):
        keyboard.add_hotkey('alt+g', self.trigger_toggle_mode)
        keyboard.add_hotkey('alt+1', self.trigger_point1)
        keyboard.add_hotkey('alt+2', self.trigger_point2)
        keyboard.add_hotkey('alt+x', self.trigger_scan)
        keyboard.add_hotkey('alt+v', self.trigger_visibility)
        keyboard.add_hotkey('alt+ctrl', self.trigger_snapshot)
        logger.info("[HOTKEYS] Хоткеи успешно зарегистрированы")