import json
import os
from dataclasses import dataclass
from typing import List, Dict

from utils_path import get_app_dir

# ==========================================
# СТРУКТУРЫ ДАННЫХ ДЛЯ ОТВЕТА
# ==========================================
@dataclass
class SignatureNode:
    """Представляет один тип камня в кластере"""
    mineral_name: str
    count: int
    base_signature: int

@dataclass
class SignatureMatch:
    """Представляет найденную комбинацию (ответ калькулятора)"""
    is_mixed: bool
    nodes: List[SignatureNode]

# ==========================================
# КАЛЬКУЛЯТОР СИГНАТУР
# ==========================================
class SignatureCalculator:
    def __init__(self, db_filename="signatures.json"):
        # Формируем абсолютный путь к папке data
        data_dir = os.path.join(get_app_dir(), "data")
        db_path = os.path.join(data_dir, db_filename)
        
        self.signatures = self._load_and_filter_signatures(db_path)

    def _load_and_filter_signatures(self, db_path) -> Dict[int, str]:
        """Загружает базу и отсеивает всё, что не относится к корабельному майнингу астероидов"""
        if not os.path.exists(db_path):
            print(f"[WARNING] Файл базы сигнатур не найден: {db_path}")
            return {}
        
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        lookup = data.get("signature_lookup", {})
        clean_sigs = {}
        
        # Ключевые слова-маркеры мусорных сигнатур (сальваж, гемы, панели)
        ignore_keywords = ["Debris", "Deposit", "Panels", "COLLISION"]
        
        for sig_str, desc in lookup.items():
            # Если описание содержит мусорные слова — пропускаем
            if any(word in desc for word in ignore_keywords):
                continue
            
            # Очищаем название (например: "Quantainium (Legendary)" -> "Quantainium")
            mineral_name = desc.split(" (")[0].strip()
            
            # Сохраняем в формате {int: str} для быстрых математических операций
            clean_sigs[int(sig_str)] = mineral_name
            
        print(f"[SUCCESS] База сигнатур загружена. Отфильтровано чистых корабельных руд: {len(clean_sigs)}")
        return clean_sigs

    def analyze(self, rs_total: int) -> List[SignatureMatch]:
        """Главный метод. Принимает число с экрана, возвращает список возможных вариантов"""
        matches = []
        
        if rs_total <= 0:
            return matches

        # ---------------------------------------------------------
        # МЕТОД 1: Расчет одиночного кластера (Быстрый проход)
        # ---------------------------------------------------------
        for base_sig, mineral in self.signatures.items():
            # Если делится нацело...
            if rs_total % base_sig == 0:
                count = rs_total // base_sig
                # ...и количество камней от 1 до 10
                if 1 <= count <= 10:
                    matches.append(SignatureMatch(
                        is_mixed=False,
                        nodes=[SignatureNode(mineral, count, base_sig)]
                    ))
        
        # По твоему ТЗ: если найден одиночный кластер, смешанный уже не ищем.
        # Это сэкономит кучу ресурсов процессора!
        if matches:
            return matches

        # ---------------------------------------------------------
        # МЕТОД 2: Расчет смешанных кластеров (Комбинаторика)
        # ---------------------------------------------------------
        # Превращаем словарь в список для перебора парами
        sig_items = list(self.signatures.items())
        n = len(sig_items)
        
        for i in range(n):
            sig1, min1 = sig_items[i]
            
            # j начинается с i+1, чтобы не проверять одну и ту же пару дважды 
            # и не проверять минерал сам с собой
            for j in range(i + 1, n): 
                sig2, min2 = sig_items[j]
                
                # Перебираем коэффициенты от 1 до 5 для каждого камня в паре
                for k1 in range(1, 6):
                    for k2 in range(1, 6):
                        # Основная формула смешанного сигнала:
                        if (sig1 * k1) + (sig2 * k2) == rs_total:
                            matches.append(SignatureMatch(
                                is_mixed=True,
                                nodes=[
                                    SignatureNode(min1, k1, sig1),
                                    SignatureNode(min2, k2, sig2)
                                ]
                            ))
                            
        return matches

# ==========================================
# ТЕСТИРОВАНИЕ ЛОГИКИ (Как это работает)
# ==========================================
if __name__ == "__main__":
    # Инициализируем наш новый модуль
    calculator = SignatureCalculator("signatures.json")
    
    # Тестовые данные из твоего описания
    test_signals = [
        10620,  # Ожидаем Beryl x3
        13540,  # Ожидаем Quantainium x2 + Bexalite x2
        9940,   # Ожидаем Savrilium x1 + Ouratite x2
        8540,   # Ожидаем Iron x2
        999999,  # Ожидаем пустой результат (ошибка сканирования)
        6000   # Ожидаем Unknown x1 #3185+3185+3185=9555, что не соответствует никакой сигнатуре в базе, но может быть реальным результатом сканирования с шумом.
    ]
    
    print("\n" + "="*50)
    for rs in test_signals:
        print(f"[SIG] СИГНАЛ НА РАДАРЕ: {rs}")
        results = calculator.analyze(rs)
        
        if not results:
            print("  [ERROR] Неизвестная сигнатура (возможно шум или мусор)")
        
        for match in results:
            mode = "СМЕШАННЫЙ" if match.is_mixed else "ОДИНОЧНЫЙ"
            out_str = " + ".join([f"{n.mineral_name} [x{n.count}]" for n in match.nodes])
            print(f"  [SUCCESS] {mode}: {out_str}")
        print("-" * 50)