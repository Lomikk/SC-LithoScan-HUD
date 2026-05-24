import sys
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
import os
import re
import difflib
import json
import datetime
from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion, RapidOCR

# ==========================================
# 1. КЛАСС MiningScanner
# ==========================================
class MiningScanner:
    """Класс для сканирования и парсинга данных об астероидах в Star Citizen"""

    # Константы класса
    ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789%. /():-'
    MINERALS = [
        "AGRICIUM", "ALUMINUM", "AMMONIA", "APHORITE", "ASLARITE", "ATACAMITE",
        "BERADOM", "BERYL", "BEXALITE", "BORASE", "CARINITE", "COBALT",
        "CONSTRUCTION MATERIAL PEBBLES", "CONSTRUCTION MATERIAL RUBBLE",
        "CONSTRUCTION MATERIAL SALVAGE", "COPPER", "CORUNDUM", "DECARI POD",
        "DIAMOND", "DOLIVINE", "FEYNMALINE", "GLACOSITE", "GOLD", "HADANITE",
        "HEPHAESTANITE", "INERT MATERIALS", "IRON", "JACLIUM", "JANALITE",
        "LARANITE", "LINDINIUM", "LINDINIUM ORE", "POTASSIUM", "QUANTANIUM",
        "QUARTZ", "RAW ICE", "ICE", "RICCITE", "SADARYX", "SALDYNIUM", "SAVRILIUM",
        "SAVRILIUM ORE", "SILICON", "STILERON", "TARANITE", "TIN", "TITANIUM",
        "TORITE", "TUNGSTEN", "WUOTAN SEED"
    ]

    SCALE_FACTOR = 4
    # Находим папку, в которой лежит этот скрипт (например, .../NewStarOCR/backend)
    _CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Если скрипт запущен из папки backend, поднимаемся на один уровень вверх в NewStarOCR
    if os.path.basename(_CURRENT_DIR) == "backend":
        PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
    else:
        PROJECT_ROOT = _CURRENT_DIR

    # Путь для отладочных картинок теперь будет внутри
    SAVE_PATH = os.path.join(PROJECT_ROOT, "RapidOCR")

    def __init__(self, use_cuda=False, device_id=0):
        """Инициализация RapidOCR и переменные класса"""
        print("Инициализация RapidOCR...")
        self.engine = RapidOCR(
            params={
                "EngineConfig.onnxruntime.use_cuda": use_cuda,
                "EngineConfig.onnxruntime.cuda_ep_cfg.device_id": device_id,

                # ПОИСК ТЕКСТА: MOBILE модель PP-OCRv4 (склеивает блоки)
                "Det.engine_type": EngineType.ONNXRUNTIME,
                "Det.model_type": ModelType.MOBILE, 
                "Det.ocr_version": OCRVersion.PPOCRV4,

                # ЧТЕНИЕ ТЕКСТА: MOBILE модель PP-OCRv5 + Строго Английский
                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Rec.lang_type": LangRec.EN,          
                "Rec.model_type": ModelType.MOBILE,   
                "Rec.ocr_version": OCRVersion.PPOCRV5, 
            }
        )

        self.dev_mode = False # Режим разработчика (переопределяется контроллером)

        # Атрибут для хранения данных астероида (доступна везде!)
        self.asteroid_data = None

        self.last_original_img = None
        self.last_resized_img = None
        self.last_raw_text = None

    # =========================================================================
    # СИСТЕМА ЛОГИРОВАНИЯ (НОВОЕ)
    # =========================================================================

        # Убедимся, что папка RapidOCR существует
        if not os.path.exists(self.SAVE_PATH):
            os.makedirs(self.SAVE_PATH)

    def _log_debug_data(self, source_info, raw_text, parsed_data):
        """Записывает сырой текст и результат парсинга в лог-файл для отладки"""
        # Путь будет: NewStarOCR\RapidOCR\scanner_debug.log
        log_file = os.path.join(self.SAVE_PATH, "scanner_debug.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ИСТОЧНИК: {source_info}\n")
            f.write("--- СЫРОЙ ТЕКСТ (OCR) ---\n")
            f.write(raw_text + "\n")
            f.write("--- РЕЗУЛЬТАТ ПАРСИНГА ---\n")
            f.write(json.dumps(parsed_data, indent=4, ensure_ascii=False) + "\n")
            f.write("="*60 + "\n\n")

    # =========================================================================
    # ВНУТРЕННИЙ МЕТОД: ЯДРО РАСПОЗНАВАНИЯ И ГРУППИРОВКИ (Новый!)
    # =========================================================================
    def _ocr_and_group_text(self, img_resized):
        """Внутренний вспомогательный метод: запускает RapidOCR на готовом массиве и группирует строки"""
        result = self.engine(img_resized)

        # Проверка на пустоту
        if not result or result.txts is None:
            return ""
        
        print(f"DEBUG (все найденные блоки): {result.txts}")

        # Извлекаем данные, фильтруем по ALLOWLIST и готовим к сортировке
        lines_data = []
        for box, text, score in zip(result.boxes, result.txts, result.scores):
            center_y = (box[0][1] + box[2][1]) / 2 
            left_x = box[0][0]

            filtered_text = "".join([c for c in text.upper() if c in self.ALLOWLIST]).strip()

            if filtered_text: 
                lines_data.append({
                    "y": center_y,
                    "x": left_x,
                    "text": filtered_text
                })

        if not lines_data:
            return ""

        # Сортируем все блоки сверху вниз (по Y)
        lines_data.sort(key=lambda item: item["y"])

        # Умная группировка строк
        grouped_lines = []
        current_line = []
        Y_THRESHOLD = 12 * self.SCALE_FACTOR 

        for item in lines_data:
            if not current_line:
                current_line.append(item)
            else:
                if abs(item["y"] - current_line[-1]["y"]) < Y_THRESHOLD:
                    current_line.append(item)
                else:
                    grouped_lines.append(current_line)
                    current_line = [item]

        if current_line:
            grouped_lines.append(current_line)

        # Собираем финальный текст
        final_texts = []
        for group in grouped_lines:
            group.sort(key=lambda item: item["x"])
            line_text = " ".join([item["text"] for item in group])
            final_texts.append(line_text)

        raw_text = "\n".join(final_texts)
        return raw_text

    # =========================================================================
    # ВХОДНЫЕ ТОЧКИ: ДЛЯ ДИСКА И ДЛЯ ОЗУ
    # =========================================================================
    def scan_image(self, image_path):
        """Принимает путь к картинке, загружает ее и отправляет на распознавание"""
        if not os.path.exists(image_path):
            print(f"Картинка не найдена: {image_path}")
            return ""

        original_img = cv2.imread(image_path)
        img_resized = cv2.resize(original_img, None, fx=self.SCALE_FACTOR, fy=self.SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)

        # Сохраняем результат для проверки
        if not os.path.exists(self.SAVE_PATH):
            os.makedirs(self.SAVE_PATH)
        cv2.imwrite(os.path.join(self.SAVE_PATH, "debug_rapid_upscale.png"), img_resized)

        return self._ocr_and_group_text(img_resized)

    def process(self, image_path):
        """Главный метод (диск): сканирует изображение по пути и парсит данные"""
        print("\n[1] Сканирование изображения с диска...")
        raw_text = self.scan_image(image_path)
        print(f"Сырой текст от RapidOCR:\n{raw_text}\n")

        print("[2] Парсинг данных...")
        self.asteroid_data = self.parse_raw_text(raw_text)
        
        # Запись общего лога только в режиме разработчика
        if self.dev_mode:
            self._log_debug_data(f"Файл: {os.path.basename(image_path)}", raw_text, self.asteroid_data)
        
        return self.asteroid_data


    # -------------------------------------------------------------------------
    # НОВЫЙ ВЫСОКОСКОРОСТНОЙ МЕТОД (ОЗУ) [1]
    # -------------------------------------------------------------------------
    def process_image(self, img_bgr):
        """Главный метод (ОЗУ): обрабатывает картинку напрямую в оперативной памяти"""
        # Кэшируем оригинальное изображение ТОЛЬКО в режиме разработчика!
        if self.dev_mode:
            self.last_original_img = img_bgr.copy()

        img_resized = cv2.resize(img_bgr, None, fx=self.SCALE_FACTOR, fy=self.SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
        
        # Кэшируем обработанное изображение ТОЛЬКО в режиме разработчика!
        if self.dev_mode:
            self.last_resized_img = img_resized.copy() 

        # Пишем отладочную картинку ТОЛЬКО в режиме разработчика!
        if self.dev_mode and os.path.exists(self.SAVE_PATH):
            cv2.imwrite(os.path.join(self.SAVE_PATH, "debug_rapid_upscale.png"), img_resized)

        print("\n[1] Распознавание изображения напрямую из ОЗУ...")
        raw_text = self._ocr_and_group_text(img_resized)
        
        # Сохраняем сырой текст распознавания ТОЛЬКО в режиме разработчика!
        if self.dev_mode:
            self.last_raw_text = raw_text 

        print("[2] Парсинг данных...")
        self.asteroid_data = self.parse_raw_text(raw_text)

        # Пишем лог-файл ТОЛЬКО в режиме разработчика!
        if self.dev_mode:
            self._log_debug_data("ОЗУ (Прямой захват)", raw_text, self.asteroid_data)

        return self.asteroid_data
    
    def save_last_scan_to_disk(self, calc_result_dict):
        """Сохраняет последние закэшированные в памяти данные на диск (по Alt+S)"""
        if self.last_original_img is None:
            print("⚠️ Нет данных последнего сканирования для создания снапшота!")
            return False

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snap_dir = os.path.join(self.SAVE_PATH, f"snapshot_{timestamp}")
        os.makedirs(snap_dir, exist_ok=True)

        try:
            # 1. Пишем сохраненные в ОЗУ картинки
            cv2.imwrite(os.path.join(snap_dir, "1_original_image.png"), self.last_original_img)
            cv2.imwrite(os.path.join(snap_dir, "2_processed_image.png"), self.last_resized_img)

            # 2. Пишем OCR-текст и результат парсинга
            log_file = os.path.join(snap_dir, "3_text_data.txt")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("--- СЫРОЙ ТЕКСТ (OCR) ---\n")
                f.write(self.last_raw_text + "\n")
                f.write("--- РЕЗУЛЬТАТ ПАРСИНГА ---\n")
                f.write(json.dumps(self.asteroid_data, indent=4, ensure_ascii=False) + "\n")

            # 3. Пишем результаты расчетов калькулятора
            calc_file = os.path.join(snap_dir, "4_calculation_results.json")
            with open(calc_file, "w", encoding="utf-8") as f:
                json.dump(calc_result_dict, f, indent=4, ensure_ascii=False)

            print(f"✅ Снапшот последнего сканирования успешно сохранен в: {snap_dir}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения снапшота на диск: {e}")
            return False

    # === НОВЫЙ МЕТОД СПЕЦИАЛЬНО ДЛЯ SNAPSHOT ===
    def _log_snapshot_data(self, raw_text, parsed_data):
        """Создает файл text_data.txt в папке снапшота"""
        if not hasattr(self, 'temp_snap_dir'): return
        
        log_file = os.path.join(self.temp_snap_dir, "3_text_data.txt")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("--- СЫРОЙ ТЕКСТ (OCR) ---\n")
            f.write(raw_text + "\n")
            f.write("--- РЕЗУЛЬТАТ ПАРСИНГА ---\n")
            f.write(json.dumps(parsed_data, indent=4, ensure_ascii=False) + "\n")
    # =========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ПАРСИНГА (ОБНОВЛЕННЫЕ И УЛУЧШЕННЫЕ)
    # =========================================================================
    def _clean_float(self, text_val):
        """Безопасно переводит строку в число. Теперь понимает запятые и пробелы в числах."""
        if not text_val: return 0.0
        # Превращаем запятые в точки (для случаев типа 9,04)
        cleaned = text_val.replace(',', '.')
        # Удаляем все, кроме цифр и точек
        cleaned = re.sub(r'[^\d\.]', '', cleaned)
        cleaned = cleaned.strip('.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _match_mineral(self, word):
        """Ищет минерал в базе, исправляя опечатки"""
        word = word.replace("(ORE)", "").replace("ORE", "").replace("(RAW)", "").replace("RAW", "").strip()
        if not word: return None
        matches = difflib.get_close_matches(word, self.MINERALS, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _normalize_composition(self, composition):
        """Умная защита от превышения 100% в составе астероида"""
        total_percent = sum(item["percent"] for item in composition)

        # Если всё в пределах нормы (допускаем микро-погрешность float 100.01)
        if total_percent <= 100.01:
            return composition

        excess = total_percent - 100.0

        # Шаг 1: Пытаемся "списать" излишек за счет INERT MATERIALS (т.к. OCR часто путает 0 и 8)
        for item in composition:
            if item["mineral"] == "INERT MATERIALS" and excess > 0:
                deduct = min(item["percent"], excess)
                item["percent"] = round(item["percent"] - deduct, 2)
                excess -= deduct

        # Шаг 2: Если излишек всё еще остался, жестко нормализуем пропорционально
        if excess > 0.01:
            current_total = sum(item["percent"] for item in composition)
            for item in composition:
                # Пропорциональное сжатие до 100%
                item["percent"] = round((item["percent"] / current_total) * 100.0, 2)

        return composition

    def parse_raw_text(self, raw_text):
        """Принимает сырой текст, возвращает словарь с готовыми переменными"""
        data = {
            "mass": 0, "resistance": 0.0, "instability": 0.0,
            "scu": 0.0, "cargo_current": 0.0, "cargo_max": 0.0,
            "composition": []
        }

        if not raw_text:
            return data

        # ==========================================
        # 1. БРОНЕБОЙНЫЙ ПОИСК БАЗОВЫХ СТАТОВ
        # ==========================================
        cleaned_text = re.sub(r'SCAN\s*RESULTS?', '', raw_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'INERT\s*MATERIALS?', '', cleaned_text, flags=re.IGNORECASE)
        
        raw_no_spaces = cleaned_text.replace(" ", "").upper()

        match_mass = re.search(r'MASS[^\d]*([\d\.,]+)', raw_no_spaces)
        if match_mass: data["mass"] = int(self._clean_float(match_mass.group(1)))

        match_res = re.search(r'RESIST(?:ANCE)?[^\d]*([\d\.,]+)', raw_no_spaces)
        if match_res: data["resistance"] = self._clean_float(match_res.group(1))

        match_inst = re.search(r'INSTABILIT(?:Y)?[^\d]*([\d\.,YO]+)', raw_no_spaces)
        if not match_inst:
            match_inst = re.search(r'INST[^\d]*([\d\.,YO]+)', raw_no_spaces)
        if match_inst: 
            val_str = match_inst.group(1).replace('Y', '.').replace('O', '0')
            data["instability"] = self._clean_float(val_str)

        # === НОВОЕ: Умный поиск SCU с поддержкой milli-SCU ===
        # (M?) в конце означает: "Захвати букву M, если она там есть"
        match_scu = re.search(r'COMP(?:OSITION)?[^\d]*([\d\.,]+)(M?)', raw_no_spaces)
        if match_scu: 
            scu_val = self._clean_float(match_scu.group(1))
            # Если регулярка поймала букву 'M' (m SCU)
            if match_scu.group(2) == 'M':
                scu_val = scu_val / 1000.0
            
            # Сохраняем, округляя до 4 знаков (чтобы не потерять точность вроде 0.4664)
            data["scu"] = round(scu_val, 4)

        match_cargo = re.search(r'CARG[O0][^\d]*([\d\.,]+)[^\d]+([\d\.,]+)', raw_no_spaces)
        if match_cargo:
            data["cargo_current"] = self._clean_float(match_cargo.group(1))
            data["cargo_max"] = self._clean_float(match_cargo.group(2))

        # ==========================================
        # 2. ПОСТРОЧНЫЙ ПОИСК МИНЕРАЛОВ
        # ==========================================
        composition_started = False
        
        for line in raw_text.split('\n'):
            line_upper = line.upper()
            
            if "LOCK" in line_upper or "TARG" in line_upper or "AUTO" in line_upper:
                break
                
            line_no_spaces = line_upper.replace(" ", "")
            if "COMPOSITION" in line_no_spaces or "COMP" in line_no_spaces:
                composition_started = True
                continue

            if composition_started:
                mineral_name = None
                
                for m in self.MINERALS:
                    if m in line_upper:
                        mineral_name = m
                        break
                
                if not mineral_name:
                    words = line_upper.replace("(ORE)", "").replace("(RAW)", "").split()
                    for word in words:
                        if len(word) > 3 and not any(c.isdigit() for c in word):
                            matched = self._match_mineral(word)
                            if matched:
                                mineral_name = matched
                                break
                                
                if mineral_name:
                    percent_val = 0.0
                    match_pct = re.search(r'([\d\.,]+)\s*%', line)
                    if match_pct:
                        percent_val = self._clean_float(match_pct.group(1))
                    else:
                        match_num = re.search(r'([\d\.,]+)', line)
                        if match_num:
                            percent_val = self._clean_float(match_num.group(1))
                    
                    while percent_val > 100:
                        percent_val = round(percent_val / 10.0, 2)

                    grade_val = 0
                    match_grade = re.search(r'\b(\d+)\s*$', line)
                    if match_grade:
                        val = match_grade.group(1)
                        if not (match_pct and self._clean_float(match_pct.group(1)) == self._clean_float(val)):
                            grade_val = int(val)

                    if percent_val > 0 or grade_val > 0 or mineral_name == "INERT MATERIALS":
                        data["composition"].append({
                            "mineral": mineral_name,
                            "percent": percent_val,
                            "grade": grade_val
                        })

        if hasattr(self, '_normalize_composition'):
            data["composition"] = self._normalize_composition(data["composition"])

        # === МАТЕМАТИЧЕСКАЯ ЗАЩИТА: Если OCR пропустил букву 'M' ===
        # В Star Citizen объем камня (SCU) никогда не превышает 1-2% от его массы.
        # Если полученный SCU аномально велик (например, больше 5% от массы),
        # значит, OCR точно пропустил букву 'M' (milli-SCU), и нам нужно поделить число на 1000.
        if data["mass"] > 0 and data["scu"] > (data["mass"] * 0.05):
            # Делим на 1000 и перезаписываем
            data["scu"] = round(data["scu"] / 1000.0, 4)    

        return data


# ==========================================
# 2. ИСПОЛЬЗОВАНИЕ КЛАССА
# ==========================================
if __name__ == "__main__":
    # Создаем экземпляр сканера
    scanner = MiningScanner()

    # Сканируем изображение (результат сохранится в scanner.asteroid_data)
    scanner.process(r"D:\Star Citizen OCR\RapidOCR\debug_rapid_upscale.png")

    # Теперь можно использовать asteroid_data где угодно!
    print("\n[3] Результаты:")
    print(f"Масса: {scanner.asteroid_data['mass']}")
    print(f"Сопротивление: {scanner.asteroid_data['resistance']}")
    print(f"Нестабильность: {scanner.asteroid_data['instability']}")
    print(f"SCU: {scanner.asteroid_data['scu']}")
    print(f"Груз: {scanner.asteroid_data['cargo_current']} / {scanner.asteroid_data['cargo_max']}")
    print(f"Состав: {scanner.asteroid_data['composition']}")