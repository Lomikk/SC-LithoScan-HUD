"""
=============================================================================
МОДУЛЬ КАЛЬКУЛЯТОРА (calculator.py)
=============================================================================

ИНТЕРФЕЙСЫ И ИСПОЛЬЗОВАНИЕ:

1. ВХОДНЫЕ ДАННЫЕ (Конфигурация):
   Используйте Data Class `CalcConfig` для передачи всех настроек.
   Пример:
       config = CalcConfig(
           system="Stanton",
           refining_method="Dinyx Solventation",
           use_grade=True,
           use_station_bonus=True
       )

2. ИНИЦИАЛИЗАЦИЯ:
   calculator = MiningCalculator(price_service, config)
   * Вы можете менять настройки "на лету" перед каждым расчетом:
     calculator.config.system = "Pyro"

3. ЗАПУСК РАСЧЕТА:
   result = calculator.analyze(scanner_data)
   Где scanner_data — это словарь от MiningScanner:
   {'scu': 32.0, 'mass': 4500, 'composition': [{'mineral': 'GOLD', 'percent': 40, 'grade': 500}, ...]}

4. ВЫХОДНЫЕ ДАННЫЕ (Результат):
   Метод analyze() возвращает объект `AnalysisResult`.
   Теперь к данным нужно обращаться через ТОЧКУ (.), а не через скобки ['']:
   - Общая прибыль:          result.totals.refined_profit
   - Плотность (aUEC/SCU):   result.totals.refined_profit_density
   - Список минералов:       result.minerals
   - Для конкретного камня:  chunk.refined.best_refining_station
=============================================================================
"""

from math import fabs
from dataclasses import dataclass, field
from typing import List, Optional

# ==========================================
# 1. СТРУКТУРЫ ДАННЫХ (ВХОД И ВЫХОД)
# ==========================================

@dataclass
class CalcConfig:
    """Настройки для калькулятора"""
    system: str = "ALL"
    yield_system: str = "ALL"
    refining_method: str = "Dinyx Solventation"
    use_grade: bool = True
    use_station_bonus: bool = True
    use_method_efficiency: bool = True

@dataclass
class RawResult:
    market_price: float
    profit: float
    profit_density_contribution: float = 0.0

@dataclass
class RefinedResult:
    mineral_after_refining_scu: float
    market_price: float
    profit: float
    yield_station_bonus: float
    best_refining_station: Optional[str]
    best_system: Optional[str]  # <--- НОВОЕ ПОЛЕ
    profit_density_contribution: float = 0.0

@dataclass
class MineralChunkResult:
    """Результат расчета по одному конкретному минералу из списка"""
    mineral_name: str
    mineral_percent: float
    grade_index: int
    grade_modifier: float
    mineral_initial_scu: float
    raw: RawResult
    refined: RefinedResult
    is_core: bool = False 

@dataclass
class TotalsResult:
    raw_profit: float = 0.0
    raw_profit_density: float = 0.0
    refined_profit: float = 0.0
    refined_profit_density: float = 0.0
    optimal_density: float = 0.0  # <--- ДОБАВЛЕНО ЯВНО
    optimal_scu: float = 0.0      # <--- ДОБАВЛЕНО ЯВНО

@dataclass
class ComparisonResult:
    profit_bonus_money: float = 0.0
    profit_bonus_percent: float = 0.0
    is_highly_profitable: bool = False

@dataclass
class AnalysisResult:
    """Главный объект, который возвращает калькулятор"""
    asteroid_total_scu: float
    asteroid_mass: float
    refining_method_name: str
    refining_method_efficiency: float
    totals: TotalsResult
    comparison: ComparisonResult
    minerals: List[MineralChunkResult] = field(default_factory=list)


# ==========================================
# 2. КЛАСС КАЛЬКУЛЯТОРА
# ==========================================

class MiningCalculator:
    def __init__(self, price_service, config: CalcConfig):
        self.price_service = price_service
        self.config = config
        self.BASE_FEE_RATE = 0.04 # Базовая ставка завода переработки (4%)

    @staticmethod
    def _get_grade_modifier(grade_index):
        # Для продажи в терминалы (aUEC) грейд сейчас не влияет.
        return 1.0

    def _calculate_mineral_chunk(self, mineral_data: dict, asteroid_total_scu: float) -> MineralChunkResult:
        """Расчет одного минерала для обоих сценариев одновременно"""
        mineral_name = mineral_data['mineral']
        mineral_percent = mineral_data['percent']
        grade_index = mineral_data.get('grade', 0)

        # 1. Исходные данные (Общие)
        mineral_initial_scu = asteroid_total_scu * (mineral_percent / 100.0)
        grade_modifier = self._get_grade_modifier(grade_index) if self.config.use_grade else 1.0

        # 2. СЦЕНАРИЙ RAW (Сырье)
        market_price_raw = self.price_service.get_market_price(mineral_name, refined=False, system=self.config.system)
        mineral_raw_profit = mineral_initial_scu * market_price_raw

        # 3. СЦЕНАРИЙ REFINED (Переработка)
        market_price_refined = self.price_service.get_market_price(mineral_name, refined=True, system=self.config.system)
        
        if self.config.use_method_efficiency:
            method_efficiency = self.price_service.get_refining_method_efficiency(self.config.refining_method)
        else:
            method_efficiency = 1.0
            
        if self.config.use_station_bonus:
            # Теперь принимаем 3 переменные (систему для поиска берем из yield_system)
            yield_station_bonus, best_station, best_system = self.price_service.get_max_yield_station_bonus(mineral_name, system=self.config.yield_system)
        else:
            yield_station_bonus, best_station, best_system = (0.0, None, None)

        # --- РАСЧЕТ ИТОГОВОГО ОБЪЕМА (SCU) ---
        mineral_after_refining_scu = (
            mineral_initial_scu 
            * method_efficiency 
            * (1.0 + yield_station_bonus)  
            * grade_modifier               
        )

        # --- РАСЧЕТ ВЫРУЧКИ И СТОИМОСТИ ПЕРЕРАБОТКИ ---
        gross_revenue = mineral_after_refining_scu * market_price_refined
        refining_cost_modifier = self.price_service.get_refining_cost_modifier(self.config.refining_method)
        refining_fee = (mineral_initial_scu * market_price_raw) * self.BASE_FEE_RATE * refining_cost_modifier
        mineral_refined_profit = gross_revenue - refining_fee

        # 4. Формируем типизированный результат
        return MineralChunkResult(
            mineral_name=mineral_name,
            mineral_percent=mineral_percent,
            grade_index=grade_index,
            grade_modifier=grade_modifier,
            mineral_initial_scu=mineral_initial_scu,
            raw=RawResult(
                market_price=market_price_raw,
                profit=mineral_raw_profit
            ),
            refined=RefinedResult(
                mineral_after_refining_scu=mineral_after_refining_scu,
                market_price=market_price_refined,
                profit=mineral_refined_profit,
                yield_station_bonus=yield_station_bonus,
                best_refining_station=best_station,
                best_system=best_system  # <--- ДОБАВЛЕНО
            )
        )

    def analyze(self, scanner_data: dict) -> Optional[AnalysisResult]:
        """Главный метод калькулятора."""
        asteroid_total_scu = scanner_data.get('scu', 0)
        composition = scanner_data.get('composition', [])

        if asteroid_total_scu <= 0 or not composition:
            return None

        method_eff = self.price_service.get_refining_method_efficiency(self.config.refining_method)
        
        # Объекты для сбора итогов
        totals = TotalsResult()
        minerals_list = []

        # --- 1. Считаем каждый минерал ---
        for item in composition:
            chunk = self._calculate_mineral_chunk(item, asteroid_total_scu)
            totals.raw_profit += chunk.raw.profit
            totals.refined_profit += chunk.refined.profit
            minerals_list.append(chunk)

        # --- 2. Считаем плотности прибыли ---
        totals.raw_profit_density = totals.raw_profit / asteroid_total_scu if asteroid_total_scu > 0 else 0
        totals.refined_profit_density = totals.refined_profit / asteroid_total_scu if asteroid_total_scu > 0 else 0

        for chunk in minerals_list:
            chunk.raw.profit_density_contribution = chunk.raw.profit / asteroid_total_scu if asteroid_total_scu > 0 else 0
            chunk.refined.profit_density_contribution = chunk.refined.profit / asteroid_total_scu if asteroid_total_scu > 0 else 0

        # --- 3. Сортировка по вкладу в плотность ---
        minerals_list.sort(key=lambda x: x.refined.profit_density_contribution, reverse=True)

        # =====================================================================
        # НОВАЯ ЛОГИКА: РАСЧЕТ "ЦЕННОГО ЯДРА" (OPTIMAL DENSITY)
        # =====================================================================
        max_pure_density = 0
        for chunk in minerals_list:
            # ИСПРАВЛЕНИЕ: Считаем плотность на 1 RAW SCU (так как трюм заполняется сырьем)
            pure_dens = chunk.refined.profit / chunk.mineral_initial_scu if chunk.mineral_initial_scu > 0 else 0
            if pure_dens > max_pure_density:
                max_pure_density = pure_dens

        optimal_profit = 0
        optimal_scu = 0
        threshold = max_pure_density * 0.40 
        
        for chunk in minerals_list:
            if "INERT" in chunk.mineral_name.upper(): 
                chunk.is_core = False
                continue
            
            pure_dens = chunk.refined.profit / chunk.mineral_initial_scu if chunk.mineral_initial_scu > 0 else 0
            
            if pure_dens >= threshold:
                chunk.is_core = True
                optimal_profit += chunk.refined.profit
                # ИСПРАВЛЕНИЕ: Прибавляем сырой объем (место в корабле), а не переработанный!
                optimal_scu += chunk.mineral_initial_scu 
            else:
                chunk.is_core = False

        totals.optimal_density = optimal_profit / optimal_scu if optimal_scu > 0 else totals.refined_profit_density
        totals.optimal_scu = optimal_scu
        # =====================================================================

        # --- 4. Сравнительная статистика ---
        comp = ComparisonResult()
        comp.profit_bonus_money = totals.refined_profit - totals.raw_profit
        comp.profit_bonus_percent = (comp.profit_bonus_money / totals.raw_profit * 100) if totals.raw_profit > 0 else 0.0
        comp.is_highly_profitable = comp.profit_bonus_percent > 20

        # Возвращаем красивый структурированный объект
        return AnalysisResult(
            asteroid_total_scu=asteroid_total_scu,
            asteroid_mass=scanner_data.get('mass', 0),
            refining_method_name=self.config.refining_method,
            refining_method_efficiency=method_eff,
            totals=totals,       # Передается уже полностью укомплектованный totals с новыми полями
            comparison=comp,
            minerals=minerals_list
        )

# ==========================================
# ИНТЕРФЕЙС (ТЕСТОВЫЙ ВЫВОД)
# ==========================================
if __name__ == "__main__":
    image_path = r"D:\Star Citizen OCR\d83edf68-ce07-4145-b98e-6f5c14e0d2b8.png"

    scanner = MiningScanner()
    scanner.process(image_path)
    scanner_data = scanner.asteroid_data

    price_service = PriceService()
    
    # Эмуляция выбора метода в интерфейсе
    selected_method = "Dinyx Solventation"
    result = analyze_asteroid(scanner_data, price_service, selected_method, use_grade=True, use_station_bonus=True, use_method_efficiency=True)

    if not result:
        print("❌ Ошибка: нет данных для расчета.")
        exit()

    # --- Красивый вывод ---
    print(f"\n{'='*130}")
    print(f"ASTEROID ANALYSIS | Volume: {result['metadata']['asteroid_total_scu']} SCU | Method: {selected_method}")
    print(f"{'='*130}")
    
    print(f"RAW SCENARIO:     {result['totals']['raw_profit']:>10,.0f} aUEC | Density: {result['totals']['raw_profit_density']:>7,.0f} aUEC/SCU")
    print(f"REFINED SCENARIO: {result['totals']['refined_profit']:>10,.0f} aUEC | Density: {result['totals']['refined_profit_density']:>7,.0f} aUEC/SCU")
    print(f"REFINING BONUS:   +{result['comparison']['profit_bonus_percent']:.1f}% (+{result['comparison']['profit_bonus_money']:,.0f} aUEC)")
    print("-" * 130)
    
    # Добавил DENSITY и увеличил общую ширину для комфорта
    print(f"{'#':<3} {'[G] MINERAL':<20} {'%':<7} | {'RAW SCU':<8} {'RAW $':<10} | {'REFINED SCU':<11} {'REFINED $':<11} | {'DENSITY':<8} | {'MODIFIERS'}")
    print("-" * 130)

    for idx, chunk in enumerate(result['minerals'], 1):
        display_name = f"[{chunk['grade_index']:>4}] {chunk['mineral_name']}"
        
        # Данные
        raw_scu = chunk['mineral_initial_scu']
        raw_profit = chunk['raw']['profit']
        
        ref_scu = chunk['refined']['mineral_after_refining_scu']
        ref_profit = chunk['refined']['profit']
        density = chunk['refined']['profit_density_contribution']
        
        # --- СБОРКА МОДИФИКАТОРОВ В ОДНУ СТРОКУ ---
        station = chunk['refined']['best_refining_station'] or "-"
        mod_parts = []
        
        # 1. Бонус станции
        if chunk['refined']['yield_station_bonus'] > 0:
            mod_parts.append(f"+{chunk['refined']['yield_station_bonus']:.0%}")
            
        # 2. Множитель грейда
        if chunk['grade_modifier'] != 1.0:
            mod_parts.append(f"x{chunk['grade_modifier']:.2f}")

        # Склеиваем: Если есть бонусы, пишем их в скобках после станции
        if station != "-" and mod_parts:
            mod_str = f"{station} ({', '.join(mod_parts)})"
        elif station != "-":
            mod_str = station
        elif mod_parts:
            mod_str = f"({', '.join(mod_parts)})"
        else:
            mod_str = "-"

        # Печать строки
        print(f"{idx:<3} {display_name:<20} {chunk['mineral_percent']:>6.2f}% | "
              f"{raw_scu:>7.2f}  {raw_profit:>10,.0f} | "
              f"{ref_scu:>10.2f}  {ref_profit:>11,.0f} | {density:>8,.0f} | {mod_str}")