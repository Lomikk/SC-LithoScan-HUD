import asyncio
import logging
import traceback
import time

from api import PriceService
from scanner import MiningScanner
from calculator import MiningCalculator, CalcConfig
from capture import ScreenCapture

logger = logging.getLogger("MinerCalc")
DEFAULT_SCAN_REGION = {'top': 337, 'left': 1408, 'width': 245, 'height': 431}

class OverlayController:
    def __init__(self):
        self.price_service = PriceService()
        self.config = CalcConfig(system="ALL", yield_system="ALL", refining_method="Dinyx Solventation")
        self.calculator = MiningCalculator(self.price_service, self.config)
        self.scanner = MiningScanner()
        self.capturer = ScreenCapture()
        
        self.server = None
        self.loop = None
        self.scan_region = DEFAULT_SCAN_REGION
        self.is_click_through = True
        self.is_scanning = False

    def set_server(self, server):
        self.server = server

    def set_loop(self, loop):
        self.loop = loop

    def _schedule_async(self, coro):
        if self.loop:
            asyncio.run_coroutine_threadsafe(coro, self.loop)

    # --- РЕАКЦИЯ НА ХОТКЕИ ---
    def toggle_mode(self):
        self.is_click_through = not self.is_click_through
        self._schedule_async(self.server.broadcast({"type": "edit_mode", "is_edit": not self.is_click_through}))

    def set_point1(self, p1):
        self._schedule_async(self.server.broadcast({"type": "status", "text": f"PT 1: {p1}", "color": "#f1c40f"}))

    def set_region(self, p1, p2):
        l, t = min(p1[0], p2[0]), min(p1[1], p2[1])
        w, h = abs(p2[0] - p1[0]), abs(p2[1] - p1[1])
        if w < 10 or h < 10:
            self._schedule_async(self.server.broadcast({"type": "status", "text": "ERR: TOO SMALL", "color": "#e74c3c"}))
            return
        
        self.scan_region = {'top': t, 'left': l, 'width': w, 'height': h}
        self._schedule_async(self.server.broadcast({"type": "status", "text": f"REGION OK", "color": "#2ecc71"}))
        self._schedule_async(self.server.broadcast({"type": "scan_frame", "t": t, "l": l, "w": w, "h": h}))

    def start_scan(self):
        if not self.is_scanning:
            self._schedule_async(self.run_scan_async())

    # --- ЛОГИКА СКАНИРОВАНИЯ ---
    async def run_scan_async(self):
        self.is_scanning = True
        await self.server.broadcast({"type": "status", "text": "CAPTURING RAM...", "color": "#f39c12"})

        try:
            # 1. Захват экрана сразу в память (в доли секунды)
            img_bgr = self.capturer.grab_region_memory(self.scan_region)
            
            await self.server.broadcast({"type": "status", "text": "ANALYZING OCR...", "color": "#f39c12"})
            
            # 2. Передаем массив пикселей в сканер (Адаптируй метод в своем scanner.py!)
            await asyncio.to_thread(self.scanner.process_image, img_bgr)
            
            if not self.scanner.asteroid_data or self.scanner.asteroid_data.get('scu', 0) == 0:
                await self.server.broadcast({"type": "status", "text": "NO ASTEROID", "color": "#e74c3c"})
                self.is_scanning = False
                return

            # 3. Расчет
            self.calculator.config = self.config
            result = self.calculator.analyze(self.scanner.asteroid_data)

            if result:
                await self.send_result_to_frontend(result)
                await self.server.broadcast({"type": "status", "text": "SCAN COMPLETE", "color": "#2ecc71"})

        except Exception as e:
            logger.error(f"[WORKER] ОШИБКА:\n{traceback.format_exc()}")
            await self.server.broadcast({"type": "status", "text": "SYSTEM ERROR", "color": "#e74c3c"})
            
        self.is_scanning = False

    # --- СЕТЕВОЙ ВВОД/ВЫВОД ---
    async def on_client_connected(self):
        methods = self.price_service.get_available_methods()
        await self.server.broadcast({
            "type": "init", 
            "methods": methods, 
            "is_edit": not self.is_click_through
        })

    async def handle_frontend_message(self, data):
        if data.get("action") == "update_config":
            self.config.refining_method = data['method']
            self.config.system = data['system']
            self.config.yield_system = data['yield_system']
            
            if hasattr(self.scanner, 'asteroid_data') and self.scanner.asteroid_data:
                result = self.calculator.analyze(self.scanner.asteroid_data)
                if result:
                    await self.send_result_to_frontend(result)
                    await self.server.broadcast({"type": "status", "text": "RECALCULATED", "color": "#2ecc71"})

    async def send_result_to_frontend(self, result):
        # 1. Отправляем сводку
        await self.server.broadcast({
            "type": "scan_totals",
            "meta_vol": result.asteroid_total_scu,
            "meta_method": result.refining_method_name[:10].upper(),
            "meta_bonus": result.comparison.profit_bonus_percent,
            "totals": {
                "t_dens": result.totals.refined_profit_density,
                "r_dens": result.totals.raw_profit_density,
                "t_prof": result.totals.refined_profit,
                "r_prof": result.totals.raw_profit,
                "opt_dens": result.totals.optimal_density, # <--- НОВОЕ
                "opt_scu": result.totals.optimal_scu       # <--- НОВОЕ
            }
        })
        
        # 2. Отправляем массив данных по минералам (ЧИСТЫЙ JSON)
        minerals_data = []
        for chunk in result.minerals:
            minerals_data.append({
                "name": chunk.mineral_name,
                "percent": chunk.mineral_percent,
                "grade": chunk.grade_index,
                "scu_ref": chunk.refined.mineral_after_refining_scu,
                "scu_raw": chunk.mineral_initial_scu,
                "dens_ref": chunk.refined.profit_density_contribution,
                "dens_raw": chunk.raw.profit_density_contribution,
                "prof_ref": chunk.refined.profit,
                "prof_raw": chunk.raw.profit,
                "station": chunk.refined.best_refining_station or "-",
                "system": chunk.refined.best_system or "Unknown", # <--- ПЕРЕДАЕМ СИСТЕМУ
                "bonus": chunk.refined.yield_station_bonus,
                "is_core": chunk.is_core
            })
            
        await self.server.broadcast({
            "type": "scan_table_data",
            "data": minerals_data
        })