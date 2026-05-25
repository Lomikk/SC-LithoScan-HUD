import asyncio
import logging
import traceback
import time
import json
import os

from api import PriceService
from scanner import MiningScanner
from calculator import MiningCalculator, CalcConfig
from capture import ScreenCapture
from signature_calculator import SignatureCalculator
from signature_scanner import SignatureScanner
from dataclasses import asdict

logger = logging.getLogger("MinerCalc")
DEFAULT_SCAN_REGION = {'top': 337, 'left': 1408, 'width': 245, 'height': 431}

# =============================================================================
# ГЛАВНЫЙ ПЕРЕКЛЮЧАТЕЛЬ ДЛЯ РАЗРАБОТЧИКА (DEV_MODE)
# True  - кэширует кадры в ОЗУ, пишет логи на диск, разрешает снапшоты по Alt+S.
# False - (для игроков) отключает логирование, кэширование картинок и экономит ОЗУ.
# =============================================================================
DEV_MODE = True 

class OverlayController:
    def __init__(self):
        self.dev_mode = DEV_MODE 
        
        # Модули астероидов
        self.price_service = PriceService()
        self.config = CalcConfig(system="ALL", yield_system="ALL", refining_method="Dinyx Solventation")
        self.calculator = MiningCalculator(self.price_service, self.config)
        self.scanner = MiningScanner()
        self.scanner.dev_mode = self.dev_mode
        
        # Модули сигнатур (НОВОЕ)
        self.sig_scanner = SignatureScanner()
        self.sig_calculator = SignatureCalculator()
        
        self.capturer = ScreenCapture()
        self.server = None
        self.loop = None
        
        # Два разных региона
        self.scan_region = DEFAULT_SCAN_REGION
        self.sig_region = {'top': 200, 'left': 800, 'width': 200, 'height': 50}
        
        self.is_click_through = True
        self.is_scanning = False
        self.is_visible = True
        self.last_result = None

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

    def set_point1(self, p1, is_signature=False):
        prefix = "SIG PT 1: " if is_signature else "PT 1: "
        self._schedule_async(self.server.broadcast({"type": "status", "text": f"{prefix}{p1}", "color": "#f1c40f"}))

    def set_region(self, p1, p2, is_signature=False):
        l, t = min(p1[0], p2[0]), min(p1[1], p2[1])
        w, h = abs(p2[0] - p1[0]), abs(p2[1] - p1[1])
        if w < 10 or h < 10:
            self._schedule_async(self.server.broadcast({"type": "status", "text": "ERR: TOO SMALL", "color": "#e74c3c"}))
            return
        
        # Если выделяли через Alt+3 / Alt+4, сохраняем в sig_region
        if is_signature:
            self.sig_region = {'top': t, 'left': l, 'width': w, 'height': h}
            prefix = "SIG REGION OK"
        # Если выделяли через Alt+1 / Alt+2, сохраняем в scan_region
        else:
            self.scan_region = {'top': t, 'left': l, 'width': w, 'height': h}
            prefix = "REGION OK"
            
        self._schedule_async(self.server.broadcast({"type": "status", "text": prefix, "color": "#2ecc71"}))
        self._schedule_async(self.server.broadcast({"type": "scan_frame", "t": t, "l": l, "w": w, "h": h}))

    def toggle_visibility(self):
        """Мгновенно прячет или показывает оверлей"""
        self.is_visible = not self.is_visible
        self._schedule_async(self.server.broadcast({"type": "visibility", "show": self.is_visible}))        

    # --- ЗАПУСК СКАНЕРОВ ---
    def start_scan(self):
        if not self.is_scanning:
            self._schedule_async(self.run_scan_async())

    def start_signature_scan(self):
        if not self.is_scanning:
            self._schedule_async(self.run_signature_scan_async())

    async def run_signature_scan_async(self):
        self.is_scanning = True
        await self.server.broadcast({"type": "status", "text": "READING SIGNATURE...", "color": "#3498db"})

        try:
            # 1. Захват маленькой области с сигнатурой
            img_bgr = self.capturer.grab_region_memory(self.sig_region)
            
            # 2. Быстрый OCR только для цифр
            rs_total = await asyncio.to_thread(self.sig_scanner.process_image, img_bgr)
            
            if rs_total == 0:
                await self.server.broadcast({"type": "status", "text": "NO SIG FOUND", "color": "#e74c3c"})
                self.is_scanning = False
                return

            # 3. Математика сигнатур
            matches = self.sig_calculator.analyze(rs_total)

            logger.info(f"[SIG DECODER] Распознана сигнатура: {rs_total}. Найдено совпадений: {len(matches)}")

            # 4. Формируем ответ для фронтенда
            response_data = []
            for match in matches:
                nodes_list = [{"mineral": n.mineral_name, "count": n.count} for n in match.nodes]
                response_data.append({
                    "is_mixed": match.is_mixed,
                    "nodes": nodes_list
                })

            await self.server.broadcast({
                "type": "sig_result",
                "rs_total": rs_total,
                "matches": response_data
            })
            
            await self.server.broadcast({"type": "status", "text": "SIG SCANNED", "color": "#2ecc71"})

        except Exception as e:
            logger.error(f"[SIG SCANNER] ОШИБКА:\n{traceback.format_exc()}")
            await self.server.broadcast({"type": "status", "text": "SIG ERROR", "color": "#e74c3c"})
            
        self.is_scanning = False        

    # --- ЛОГИКА СКАНЕРА АСТЕРОИДОВ ---
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
            result = self.calculator.analyze(self.scanner.asteroid_data)

            if result:
                # Кэшируем результат только если включен режим разработчика
                if self.dev_mode:
                    self.last_result = result 
                    
                await self.send_result_to_frontend(result)
                await self.server.broadcast({"type": "status", "text": "SCAN COMPLETE", "color": "#2ecc71"})

        except Exception as e:
            logger.error(f"[WORKER] ОШИБКА:\n{traceback.format_exc()}")
            await self.server.broadcast({"type": "status", "text": "SYSTEM ERROR", "color": "#e74c3c"})
            
        self.is_scanning = False

    def save_debug_snapshot(self):
        """Запуск скана с сохранением всех данных в папку (Вызывается по Alt+S)"""
        if not self.is_scanning:
            self._schedule_async(self.run_snapshot_async())

    async def run_snapshot_async(self):
        self.is_scanning = True
        
        # Если режим разработчика выключен, снапшот заблокирован
        if not self.dev_mode:
            await self.server.broadcast({"type": "status", "text": "DEV MODE DISABLED", "color": "#e74c3c"})
            self.is_scanning = False
            return
        
        if not self.last_result:
            await self.server.broadcast({"type": "status", "text": "NO RECENT SCAN DATA", "color": "#e67e22"})
            self.is_scanning = False
            return

        await self.server.broadcast({"type": "status", "text": "SAVING SNAPSHOT FROM CACHE...", "color": "#f1c40f"})

        try:
            # Превращаем сохраненный датакласс в JSON-словарь
            calc_dict = asdict(self.last_result)
            
            # Просим сканер записать все сохраненные в ОЗУ файлы на диск
            # Специфика asyncio: запускаем синхронную запись файла в отдельном потоке
            success = await asyncio.to_thread(self.scanner.save_last_scan_to_disk, calc_dict)

            if success:
                await self.server.broadcast({"type": "status", "text": "SNAPSHOT COPIED FROM CACHE", "color": "#2ecc71"})
            else:
                await self.server.broadcast({"type": "status", "text": "WRITE ERROR", "color": "#e74c3c"})

        except Exception as e:
            logger.error(f"[WORKER] ОШИБКА SNAPSHOT:\n{traceback.format_exc()}")
            await self.server.broadcast({"type": "status", "text": "SNAPSHOT ERROR", "color": "#e74c3c"})
            
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
                    # Кэшируем результат только если включен режим разработчика
                    if self.dev_mode:
                        self.last_result = result 
                        
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