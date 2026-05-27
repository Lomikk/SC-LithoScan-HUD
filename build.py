import os
import sys
import json
import shutil
import subprocess
from datetime import datetime

# =======================================================
# НАСТРОЙКИ ПУТЕЙ И ПАПОК
# ==========================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# Временная папка для мусора от компиляторов
TEMP_BUILD_DIR = os.path.join(ROOT_DIR, "build_temp")
# Папка, куда будут складываться готовые .exe файлы
RELEASES_DIR = os.path.join(ROOT_DIR, "Releases")

BUILD_NUM_FILE = os.path.join(ROOT_DIR, "build_number.txt")

def get_next_build_number():
    """Читает и увеличивает номер сборки"""
    build_num = 1
    if os.path.exists(BUILD_NUM_FILE):
        with open(BUILD_NUM_FILE, "r") as f:
            try:
                build_num = int(f.read().strip()) + 1
            except ValueError:
                pass
    with open(BUILD_NUM_FILE, "w") as f:
        f.write(str(build_num))
    return build_num

def get_app_version():
    """Достает текущую версию из package.json"""
    try:
        with open(os.path.join(FRONTEND_DIR, "package.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("version", "1.0.0")
    except:
        return "1.0.0"

def clean_temp_folders():
    """Удаляет временные папки для идеальной чистоты"""
    print("Очистка временных файлов...")
    folders_to_remove = [
        TEMP_BUILD_DIR,
        os.path.join(FRONTEND_DIR, "dist"),
        os.path.join(FRONTEND_DIR, "backend-bin")
    ]
    for folder in folders_to_remove:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"  [!] Не удалось удалить {folder}: {e}")

def run_command(cmd, cwd):
    """Выполняет консольную команду с перехватом вывода"""
    process = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(f"  > {line.strip()}")
    process.wait()
    if process.returncode != 0:
        print("\n[ERROR] ОШИБКА ПРИ ВЫПОЛНЕНИИ КОМАНДЫ!")
        sys.exit(1)

def main():
    print("=" * 60)
    print("ЗАПУСК АВТОМАТИЧЕСКОЙ СБОРКИ LITHOSCAN HUD")
    print("=" * 60)

    # 0. Инициализация
    os.makedirs(TEMP_BUILD_DIR, exist_ok=True)
    os.makedirs(RELEASES_DIR, exist_ok=True)
    
    build_num = get_next_build_number()
    version = get_app_version()
    current_date = datetime.now().strftime("%Y-%m-%d")
    final_exe_name = f"LithoScan_HUD_v{version}_build-{build_num}_{current_date}.exe"
    
    print(f"Подготовка сборки: {final_exe_name}")

    # 1. Сборка Backend (Питон)
    print("\n[1/4] Компиляция Python Backend...")
    py_work = os.path.join(TEMP_BUILD_DIR, "py_work")
    py_dist = os.path.join(TEMP_BUILD_DIR, "py_dist")
    
    # Ищем локальный pyinstaller внутри виртуального окружения venv, чтобы сборка была чистой
    venv_pyinstaller = os.path.join(BACKEND_DIR, "venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = f'"{venv_pyinstaller}"'
    else:
        pyinstaller_bin = "pyinstaller" # Откат на глобальный, если venv не настроен
    
    # Явно запрещаем упаковку тяжелых и ненужных библиотек
    exclude_args = (
        "--exclude-module PyQt5 --exclude-module PyQt5.QtCore --exclude-module PyQt5.QtGui --exclude-module PyQt5.QtWidgets "
        "--exclude-module matplotlib --exclude-module scipy --exclude-module pandas --exclude-module IPython --exclude-module jedi "
        "--exclude-module wx --exclude-module tornado --exclude-module pygments --exclude-module sqlite3 --exclude-module sympy"
    )

    pyinstaller_cmd = (
        f'{pyinstaller_bin} --clean --noconsole --onedir --name "lithoscan_backend" {exclude_args} '
        f'--collect-all rapidocr_onnxruntime --collect-all rapidocr --collect-all onnxruntime --collect-all cv2 '
        f'--workpath "{py_work}" --distpath "{py_dist}" --specpath "{TEMP_BUILD_DIR}" main.py'
    )
    run_command(pyinstaller_cmd, cwd=BACKEND_DIR)

    # 2. Интеграция - Копируем всю скомпилированную папку целиком
    print("\n[2/4] Копирование ядра и баз данных в Frontend...")
    fe_backend_bin = os.path.join(FRONTEND_DIR, "backend-bin")
    if os.path.exists(fe_backend_bin):
        shutil.rmtree(fe_backend_bin)
        
    # Копируем всё дерево папки дистрибутива Питона
    shutil.copytree(os.path.join(py_dist, "lithoscan_backend"), fe_backend_bin)

    # Копируем папку data со всеми ценами и сигнатурами внутрь backend-bin
    fe_data_dir = os.path.join(fe_backend_bin, "data")
    shutil.copytree(os.path.join(BACKEND_DIR, "data"), fe_data_dir)

    # 3. Сборка Frontend (Electron)
    print("\n[3/4] Упаковка интерфейса и создание инсталлятора...")
    run_command("npm run dist", cwd=FRONTEND_DIR)

    # 4. Перемещение результата и переименование
    print("\n[4/4] Формирование релизного файла...")
    fe_dist_dir = os.path.join(FRONTEND_DIR, "dist")
    
    # Ищем сгенерированный .exe в папке frontend/dist
    installer_path = None
    for file in os.listdir(fe_dist_dir):
        if file.endswith(".exe") and "Setup" in file:
            installer_path = os.path.join(fe_dist_dir, file)
            break

    if installer_path:
        final_dest = os.path.join(RELEASES_DIR, final_exe_name)
        shutil.move(installer_path, final_dest)
        print(f"[SUCCESS] Файл сохранен: {final_dest}")
    else:
        print("[ERROR] ОШИБКА: Инсталлятор не найден в папке dist!")

    # 5. Уборка мусора
    clean_temp_folders()
    print("\nПроект очищен. Сборка завершена!")

if __name__ == "__main__":
    main()