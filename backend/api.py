"""
=============================================================================
МОДУЛЬ РАБОТЫ С ДАННЫМИ И API (api.py)
=============================================================================

ОПИСАНИЕ:
Этот модуль отвечает за хранение, выдачу и обновление всех констант, 
цен и модификаторов в игре. Он изолирует калькулятор от интернета и файлов.

ИНТЕРФЕЙСЫ:
- Калькулятор запрашивает цены через `get_market_price(name, refined, system)`
- Калькулятор запрашивает бонусы станций через `get_max_yield_station_bonus()`
- Интерфейс обновляет базу данных через `update_all_data()`
=============================================================================
"""

import json
import os
import requests
import datetime

from utils_path import get_app_dir

class PriceService:
    """Сервис для работы с API (цены, методы, бонусы) с поддержкой локального кэша"""

    def __init__(self):
        # 1. Создаем папку data для порядка
        self.data_dir = os.path.join(get_app_dir(), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.prices_file = os.path.join(self.data_dir, "prices.json")
        self.refining_file = os.path.join(self.data_dir, "refining_methods.json")
        self.yield_file = os.path.join(self.data_dir, "yield_bonuses.json")

        self.last_update_time = "Never"
        
        # 2. Загружаем данные из файлов
        self.reload_local_data()

    # ==========================================
    # БАЗОВЫЕ УТИЛИТЫ И ОЧИСТКА
    # ==========================================
    @staticmethod
    def _clean_mineral_name(raw_name: str) -> str:
        """Бронебойная очистка мусора из названий UEXCorp"""
        name = raw_name.upper()
        junk_words = ["(ORE)", "(RAW)", "(PURE)", "(UNREFINED)", " ORE", " RAW", " PURE"]
        for word in junk_words:
            name = name.replace(word, "")
        name = name.strip()
        if "QUANTAINIUM" in name: 
            return "QUANTANIUM"
        return name

    def _load_json(self, filepath, default_data):
        """Безопасная загрузка JSON с возвратом дефолтных данных при сбое"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"[WARNING] Ошибка формата в {os.path.basename(filepath)}. Используются данные по умолчанию.")
        
        # Если файла нет или он сломан - создаем новый
        self._save_json(filepath, default_data)
        return default_data

    def _save_json(self, filepath, data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Ошибка сохранения в {os.path.basename(filepath)}: {e}")

    def reload_local_data(self):
        """Горячая загрузка данных с жесткого диска (Без перезапуска программы!)"""
        self._prices = self._load_json(self.prices_file, self._get_default_prices())
        self._refining_methods = self._load_json(self.refining_file, self._get_default_refining_methods())
        self._yield_bonuses = self._load_json(self.yield_file, {})
        
        # Пытаемся вытащить время последнего обновления из файла цен
        self.last_update_time = self._prices.get("_metadata", {}).get("last_updated", "Unknown")
        print(f"Локальные базы данных загружены. Последнее обновление API: {self.last_update_time}")

    # ==========================================
    # ИНТЕРФЕЙСЫ ДЛЯ КАЛЬКУЛЯТОРА
    # ==========================================
    def get_available_methods(self):
        return sorted([k for k in self._refining_methods.keys() if k != "_metadata"])    

    def get_market_price(self, mineral_name, refined=False, system="ALL"):
        mineral = self._clean_mineral_name(mineral_name)
        if mineral in self._prices:
            state = "refined" if refined else "unrefined"
            prices_by_system = self._prices[mineral].get(state, {})
            return prices_by_system.get(system, prices_by_system.get("ALL", 0))
        return 0

    def get_refining_method_efficiency(self, method_name):
        method_data = self._refining_methods.get(method_name, {})
        return method_data.get("yield", 1.0) if isinstance(method_data, dict) else 1.0

    def get_refining_cost_modifier(self, method_name):
        method_data = self._refining_methods.get(method_name, {})
        return method_data.get("cost", 1.0) if isinstance(method_data, dict) else 1.0

    def get_max_yield_station_bonus(self, mineral_name, system="ALL"):
        mineral = self._clean_mineral_name(mineral_name)
        bonuses = self._yield_bonuses.get(mineral, [])
        
        if not bonuses or isinstance(bonuses, dict): 
            return (0.0, None, None)

        best_bonus, best_station, best_system = -float('inf'), None, None

        for b in bonuses:
            if system != "ALL" and b["system"].upper() != system.upper():
                continue
            if b["bonus"] > best_bonus:
                best_bonus, best_station, best_system = b["bonus"], b["station"], b["system"]

        return (best_bonus, best_station, best_system) if best_station else (0.0, None, None)

    # ==========================================
    # ОБНОВЛЕНИЕ ДАННЫХ ИЗ ИНТЕРНЕТА (UEXCorp)
    # ==========================================
    def update_all_data(self) -> str:
        """Запускает обновление и возвращает статус для интерфейса"""
        print("\n=== ЗАПРОС К UEXCORP API ===")
        try:
            # Если связи нет, requests выбросит исключение, и старые данные не пострадают
            self._fetch_and_save_prices()  
            self._fetch_and_save_yields()     
            
            self.last_update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self._prices["_metadata"] = {"last_updated": self.last_update_time}
            self._save_json(self.prices_file, self._prices)
            
            print(f"=== ОБНОВЛЕНИЕ УСПЕШНО ({self.last_update_time}) ===\n")
            return f"SUCCESS: {self.last_update_time}"
        except Exception as e:
            err_msg = f"API ERROR: {str(e)[:40]}..."
            print(f"[ERROR] {err_msg}\nИспользуются старые локальные данные.")
            return err_msg

    def _fetch_and_save_prices(self):
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (lithoscan-hud)'})
        BASE_URL = "https://api.uexcorp.space/2.0"
        TIMEOUT = 10 

        # 1. Загружаем терминалы
        term_resp = session.get(f"{BASE_URL}/terminals", timeout=TIMEOUT).json()
        terminal_systems = {t['id']: (t.get('star_system_name') or "Unknown") for t in term_resp.get('data', [])}

        # 2. База товаров
        comm_resp = session.get(f"{BASE_URL}/commodities", timeout=TIMEOUT).json()
        new_prices = {}
        id_to_mineral = {}
        
        for item in comm_resp.get('data', []):
            if item.get('is_mineral') == 1 or item.get('is_extractable') == 1 or item.get('is_raw') == 1:
                base_name = self._clean_mineral_name(item['name'])
                if base_name not in new_prices:
                    new_prices[base_name] = {"unrefined": {"ALL": 0}, "refined": {"ALL": 0}}

                state = "unrefined" if item.get('is_raw') == 1 else "refined"
                id_to_mineral[item['id']] = {"base_name": base_name, "state": state}
                
                avg_price = float(item.get('price_sell', 0))
                if avg_price > 0:
                    new_prices[base_name][state]["ALL"] = avg_price

        # Вспомогательная функция
        def process_prices(data_list):
            for p in data_list:
                c_id, price_sell = p.get('id_commodity'), float(p.get('price_sell', 0))
                if c_id in id_to_mineral and price_sell > 0:
                    info = id_to_mineral[c_id]
                    b_name, state = info['base_name'], info['state']
                    sys_name = terminal_systems.get(p.get('id_terminal'), "ALL")

                    if sys_name not in new_prices[b_name][state]:
                        new_prices[b_name][state][sys_name] = 0

                    if price_sell > new_prices[b_name][state][sys_name]:
                        new_prices[b_name][state][sys_name] = price_sell
                    if price_sell > new_prices[b_name][state]["ALL"]:
                        new_prices[b_name][state]["ALL"] = price_sell

        # 3. Живые цены
        process_prices(session.get(f"{BASE_URL}/commodities_prices_all", timeout=TIMEOUT).json().get('data', []))
        process_prices(session.get(f"{BASE_URL}/commodities_raw_prices_all", timeout=TIMEOUT).json().get('data', []))

        # Записываем ТОЛЬКО если не было ошибок
        self._prices = new_prices
        self._save_json(self.prices_file, self._prices)
        session.close()
            
    def _fetch_and_save_yields(self):
        url = "https://api.uexcorp.space/2.0/refineries_yields"
        data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (lithoscan-hud)'}, timeout=10).json().get('data', [])
        
        new_yields = {}
        for entry in data:
            clean_mineral = self._clean_mineral_name(entry.get('commodity_name', ''))
            bonus = float(entry.get('value', 0)) / 100.0
            system_name = entry.get('star_system_name', 'Unknown')
            
            full_station = entry.get('space_station_name')
            city = entry.get('city_name')
            
            if full_station:
                if full_station.startswith(("MIC-", "ARC-", "HUR-", "CRU-")): short_station = full_station.split(' ')[0]
                elif '(' in full_station: short_station = full_station.split('(')[0].strip()
                else: short_station = full_station.replace(" Station", "").strip()
            elif city: short_station = city
            else: short_station = "Unknown"
            
            if clean_mineral not in new_yields: new_yields[clean_mineral] = []
            new_yields[clean_mineral].append({"station": short_station, "system": system_name, "bonus": bonus})
        
        self._yield_bonuses = new_yields
        self._save_json(self.yield_file, self._yield_bonuses)

    # ДЕФОЛТНЫЕ МОКИ (На случай самого первого запуска без интернета)
    @staticmethod
    def _get_default_prices():
        return {
            "QUANTANIUM": {"unrefined": {"ALL": 24200}, "refined": {"ALL": 170000}},
            "GOLD": {"unrefined": {"ALL": 2672}, "refined": {"ALL": 33000}},
            "INERT MATERIALS": {"unrefined": {"ALL": 0}, "refined": {"ALL": 0}}
        }

    @staticmethod
    def _get_default_refining_methods():
        return {
            "Dinyx Solventation": {"yield": 0.95, "cost": 1.0, "time": 4.0},
            "Ferron Exchange": {"yield": 0.98, "cost": 2.2, "time": 1.5}
        }