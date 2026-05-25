import cv2
import re
from rapidocr import RapidOCR, EngineType, ModelType, OCRVersion

class SignatureScanner:
    """Легкий OCR-модуль для считывания только цифр сигнатуры"""
    def __init__(self, use_cuda=False):
        self.engine = RapidOCR(
            params={
                "EngineConfig.onnxruntime.use_cuda": use_cuda,
                "Det.model_type": ModelType.MOBILE, 
                "Rec.model_type": ModelType.MOBILE,   
            }
        )
        self.SCALE_FACTOR = 3

    def process_image(self, img_bgr):
        """Обрабатывает изображение и возвращает найденное число (сигнатуру)"""
        # Увеличиваем картинку для лучшего распознавания мелких цифр HUD
        img_resized = cv2.resize(img_bgr, None, fx=self.SCALE_FACTOR, fy=self.SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
        
        result = self.engine(img_resized)
        if not result or not result.txts:
            return 0
            
        # Объединяем весь найденный текст
        combined_text = " ".join(result.txts)
        
        # 1. Заменяем частые ошибки OCR (буквы O на нули)
        combined_text = combined_text.replace('O', '0').replace('o', '0')
        
        # 2. ИСПРАВЛЕНИЕ: Удаляем запятые и точки, чтобы 11,700 стало 11700
        combined_text = combined_text.replace(',', '').replace('.', '')
        
        # 3. Ищем непрерывные блоки цифр
        numbers = re.findall(r'\d+', combined_text)
        
        if not numbers:
            return 0
            
        # Сигнатуры в игре обычно от 1700 до 50000+. 
        # Отфильтровываем случайный мусор (цифры короче 3 знаков)
        valid_nums = [int(n) for n in numbers if len(n) >= 3]
        if valid_nums:
            return max(valid_nums) # Берем максимальное из найденного
            
        return 0