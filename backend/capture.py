import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def grab_region_memory(self, region: dict):
        """
        Захватывает регион и возвращает изображение в оперативной памяти 
        в формате BGR (стандарт для OpenCV), минуя жесткий диск.
        """
        # mss возвращает объект, который мы превращаем в numpy-массив
        sct_img = self.sct.grab(region)
        img_np = np.array(sct_img)
        
        # Конвертируем BGRA (с альфа-каналом) в BGR
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        return img_bgr