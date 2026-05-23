import time
from api import PriceService

def manual_update():
    print("🚀 Запуск ручного обновления баз данных...")
    start_time = time.time()

    try:
        # Инициализируем сервис (он сам подхватит существующие файлы или создаст дефолтные)
        service = PriceService()
        
        # Запускаем полное обновление (Цены + Бонусы станций)
        # Этот метод мы писали в api.py, он вызывает update_prices_from_web и update_yield_bonuses
        service.update_all_data()

        duration = time.time() - start_time
        print(f"\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print(f"⏱ Затрачено времени: {duration:.2f} сек.")
        print(f"📁 Файлы 'prices.json' и 'yield_bonuses.json' обновлены актуальными данными из Pyro и Stanton.")

    except Exception as e:
        print(f"\n❌ ПРОИЗОШЛА ОШИБКА ПРИ ОБНОВЛЕНИИ:")
        print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_update()
    input("\nНажмите Enter, чтобы выйти...")