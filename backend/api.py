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

class PriceService:
    """Сервис для получения цен, методов переработки и бонусов выхода"""

    def __init__(self, prices_file="prices.json", refining_file="refining_methods.json", yield_file="yield_bonuses.json"):
        self.prices_file = prices_file
        
        # 1. Загружаем цены
        if os.path.exists(self.prices_file):
            self._prices = self._load_json(self.prices_file)
        else:
            self._prices = self._get_default_prices()
            self._save_prices_to_json()

        # 2. Загружаем методы переработки (с защитой от отсутствия файла)
        if os.path.exists(refining_file):
            self._refining_methods = self._load_json(refining_file)
        else:
            self._refining_methods = self._get_default_refining_methods()
            self._save_json(refining_file, self._refining_methods)

        # 3. Загружаем бонусы
        self._yield_bonuses = self._load_json(yield_file) if os.path.exists(yield_file) else {}

    # ==========================================
    # УТИЛИТЫ И ДЕФОЛТНЫЕ ЗНАЧЕНИЯ
    # ==========================================

    @staticmethod
    def _load_json(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Ошибка чтения {filepath}: {e}")
            return {}

    def _save_prices_to_json(self):
        self._save_json(self.prices_file, self._prices)

    def _save_json(self, filepath, data):
        """Универсальный метод сохранения данных в JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✅ Данные сохранены в {filepath}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в {filepath}: {e}")

    @staticmethod
    def _get_default_prices():
        """Встроенные цены по умолчанию на случай первого запуска без интернета."""
        return {
            "QUANTANIUM": {
                "unrefined": {"ALL": 24200, "Stanton": 24200, "Pyro": 21000},
                "refined": {"ALL": 170000, "Stanton": 170000, "Nyx": 175000}
            },
            "GOLD": {
                "unrefined": {"ALL": 2672, "Stanton": 2672},
                "refined": {"ALL": 33000, "Stanton": 33000}
            },
            "INERT MATERIALS": {
                "unrefined": {"ALL": 0, "Stanton": 0},
                "refined": {"ALL": 0, "Stanton": 0}
            }
        }

    @staticmethod
    def _get_default_refining_methods():
        """Базовые методы переработки, если файла нет"""
        return {
            "Dinyx Solventation": {"yield": 0.95, "cost": 1.0, "time": 4.0},
            "Ferron Exchange": {"yield": 0.98, "cost": 2.2, "time": 1.5},
            "Gaskin Process": {"yield": 0.96, "cost": 1.5, "time": 2.5},
            "Pyrometric Chromalizing": {"yield": 0.97, "cost": 1.8, "time": 2.0},
            "Cormack Method": {"yield": 0.94, "cost": 1.1, "time": 3.5},
            "Xanthule Process": {"yield": 0.93, "cost": 1.2, "time": 3.0},
        }

    # ==========================================
    # ИНТЕРФЕЙСЫ ДЛЯ КАЛЬКУЛЯТОРА
    # ==========================================

    def get_available_methods(self):
        """Возвращает отсортированный список названий методов для выпадающего списка GUI"""
        return sorted(self._refining_methods.keys())    

    def get_market_price(self, mineral_name, refined=False, system="ALL"):
        """Возвращает цену за 1 SCU для минерала."""
        mineral = mineral_name.upper()
        if mineral in self._prices:
            state = "refined" if refined else "unrefined"
            prices_by_system = self._prices[mineral].get(state, {})
            
            # Ищем цену для конкретной системы. Если ее нет, отдаем ALL. Если и ALL нет, отдаем 0.
            return prices_by_system.get(system, prices_by_system.get("ALL", 0))
        return 0

    def get_refining_method_efficiency(self, method_name):
        """Возвращает коэффициент выхода (Yield)"""
        method_data = self._refining_methods.get(method_name, 1.0)
        if isinstance(method_data, dict):
            return method_data.get("yield", 1.0)
        return method_data # поддержка старого формата

    def get_refining_cost_modifier(self, method_name):
        """Возвращает множитель стоимости переработки"""
        method_data = self._refining_methods.get(method_name)
        if isinstance(method_data, dict):
            return method_data.get("cost", 1.0)
        return 1.0

    def get_refining_time_modifier(self, method_name):
        """Возвращает множитель времени (для красоты в GUI)"""
        method_data = self._refining_methods.get(method_name)
        if isinstance(method_data, dict):
            return method_data.get("time", 1.0)
        return 1.0

    def get_max_yield_station_bonus(self, mineral_name, system="ALL"):
        """Возвращает лучший бонус для минерала: (бонус, станция, система)"""
        mineral = mineral_name.upper()
        
        # Получаем список всех бонусов для этого минерала
        bonuses = self._yield_bonuses.get(mineral, [])
        
        # Защита на случай, если локально лежит старый файл yield_bonuses.json
        if isinstance(bonuses, dict):
            print("⚠️ Обнаружен старый формат базы бонусов! Нажми 'Обновить БД' в интерфейсе.")
            return (0.0, None, None)

        if not bonuses:
            return (0.0, None, None)

        best_bonus = -float('inf')
        best_station = None
        best_system = None

        for b in bonuses:
            # Фильтрация по системе, если выбрана конкретная (не "ALL")
            if system != "ALL" and b["system"].upper() != system.upper():
                continue

            if b["bonus"] > best_bonus:
                best_bonus = b["bonus"]
                best_station = b["station"]
                best_system = b["system"]

        if best_station:
            return (best_bonus, best_station, best_system)
        return (0.0, None, None)


    def update_yield_bonuses(self):
        print("⏳ Загрузка и умная конвертация бонусов из API...")
        url = "https://api.uexcorp.space/2.0/refineries_yields"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json().get('data', [])
            
            # Новая структура: {"GOLD": [{"station": "MIC-L1", "system": "Stanton", "bonus": 0.09}, ...]}
            new_yields = {}
            
            for entry in data:
                # 1. Очистка имени минерала
                raw_mineral = entry.get('commodity_name', '').upper()
                junk_words = ["(ORE)", "(RAW)", "(PURE)", "ORE", "RAW", "PURE"]
                clean_mineral = raw_mineral
                for word in junk_words:
                    clean_mineral = clean_mineral.replace(word, "")
                clean_mineral = clean_mineral.strip()
                if "QUANTAINIUM" in clean_mineral: clean_mineral = "QUANTANIUM"

                # 2. Парсинг значений
                bonus = float(entry.get('value', 0)) / 100.0
                system_name = entry.get('star_system_name', 'Unknown')
                
                # 3. Умное сокращение названия станции
                full_station = entry.get('space_station_name')
                city = entry.get('city_name')
                
                if full_station:
                    # Например: "MIC-L5 Modern Icarus Station" -> "MIC-L5"
                    if full_station.startswith(("MIC-", "ARC-", "HUR-", "CRU-")):
                        short_station = full_station.split(' ')[0]
                    # Например: "Nyx Gateway (Pyro)" -> "Nyx Gateway"
                    elif '(' in full_station:
                        short_station = full_station.split('(')[0].strip()
                    # Например: "Checkmate Station" -> "Checkmate"
                    else:
                        short_station = full_station.replace(" Station", "").strip()
                elif city:
                    # Например: "Levski"
                    short_station = city
                else:
                    short_station = "Unknown"
                
                # 4. Сохранение в словарь
                if clean_mineral not in new_yields:
                    new_yields[clean_mineral] = []
                    
                new_yields[clean_mineral].append({
                    "station": short_station,
                    "system": system_name,
                    "bonus": bonus
                })
            
            self._yield_bonuses = new_yields
            self._save_json("yield_bonuses.json", self._yield_bonuses)
            print(f"✅ Бонусы обновлены! Ресурсов в базе: {len(new_yields)}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке бонусов: {e}")

    # ==========================================
    # ОБНОВЛЕНИЕ ДАННЫХ ИЗ ИНТЕРНЕТА
    # ==========================================

    def update_all_data(self):
        """Запускает полное обновление всех справочников и цен"""
        print("\n=== НАЧАЛО ПОЛНОГО ОБНОВЛЕНИЯ БАЗЫ ДАННЫХ ===")
        self.update_prices_from_web()  
        self.update_yield_bonuses()     
        print("=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО ===\n")

    def update_prices_from_web(self):
        print("⏳ Запуск динамического обновления цен...")
        
        # --- ПРОВЕРКА СВЯЗИ ---
        try:
            import socket
            socket.create_connection(("api.uexcorp.space", 443), timeout=5)
        except OSError:
            print("❌ ОШИБКА: Нет связи с сервером UEXCorp.")
            print("👉 Проверь: Включен ли VPN? Работает ли интернет?")
            return # Прекращаем выполнение, чтобы не копить ошибки
        new_prices = {}
        id_to_mineral = {}
        
        session = requests.get_session() if hasattr(requests, 'get_session') else requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (MinerCalc/1.0)'})
        TIMEOUT = 30 
        BASE_URL = "https://api.uexcorp.space/2.0"

        try:
            # 1. Загружаем терминалы
            print("--- 1. Синхронизация терминалов...")
            terminal_systems = {}
            try:
                term_resp = session.get(f"{BASE_URL}/terminals", timeout=TIMEOUT)
                for t in term_resp.json().get('data', []):
                    terminal_systems[t['id']] = t.get('star_system_name') or "Unknown"
            except Exception as e:
                print(f"⚠️ Ошибка терминалов: {e}")

            # 2. Загружаем справочник (Динамическое определение ресурсов)
            print("--- 2. Динамический анализ ресурсов...")
            comm_resp = session.get(f"{BASE_URL}/commodities", timeout=TIMEOUT)
            
            for item in comm_resp.json().get('data', []):
                # Фильтруем только то, что относится к добыче
                # is_mineral - минералы, is_extractable - то что добывается
                if item.get('is_mineral') == 1 or item.get('is_extractable') == 1 or item.get('is_raw') == 1:
                    
                    raw_name = item['name'].upper()
                    
                    # Очистка имени от мусора типа (RAW), (ORE), (UNREFINED)
                    # чтобы "GOLD (RAW)" и "GOLD" превратились в один ключ "GOLD"
                    base_name = raw_name.replace("(RAW)", "").replace("(ORE)", "")\
                                        .replace("(UNREFINED)", "").replace("(PURE)", "").strip()
                    
                    # Маппинг Quantainium (для совместимости с твоим кодом)
                    if "QUANTAINIUM" in base_name:
                        base_name = "QUANTANIUM"

                    # Инициализируем структуру в new_prices, если ресурса еще нет
                    if base_name not in new_prices:
                        new_prices[base_name] = {
                            "unrefined": {"ALL": 0}, 
                            "refined": {"ALL": 0}
                        }

                    # Определяем состояние
                    state = "unrefined" if item.get('is_raw') == 1 else "refined"
                    id_to_mineral[item['id']] = {"base_name": base_name, "state": state}
                    
                    # Записываем базовую цену как стартовую
                    avg_price = float(item.get('price_sell', 0))
                    if avg_price > 0:
                        new_prices[base_name][state]["ALL"] = avg_price

            # Вспомогательная функция обработки цен
            def process_prices(data_list):
                for p in data_list:
                    c_id = p.get('id_commodity')
                    price_sell = float(p.get('price_sell', 0))
                    
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

            # 3. Загружаем живые цены
            print(f"--- 3. Загрузка цен для {len(new_prices)} обнаруженных ресурсов...")
            
            refined_resp = session.get(f"{BASE_URL}/commodities_prices_all", timeout=TIMEOUT)
            process_prices(refined_resp.json().get('data', []))

            unrefined_resp = session.get(f"{BASE_URL}/commodities_raw_prices_all", timeout=TIMEOUT)
            process_prices(unrefined_resp.json().get('data', []))

            # 5. Сохранение
            self._prices = new_prices
            self._save_prices_to_json()
            print(f"✅ Успешно обновлено! Найдено ресурсов: {len(new_prices)}")

        except Exception as e:
            print(f"❌ Ошибка динамического обновления: {e}")
        finally:
            session.close()