@echo off
echo ==================================================
echo   INITIALIZING STAR CITIZEN OVERLAY SETUP...
echo ==================================================

:: 1. ПРОВЕРКА И ЗАПРОС НА УСТАНОВКУ NODE.JS
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Node.js or npm is not detected on your system.
    echo [INFO] Node.js is required to install and run the Electron frontend.
    echo.
    
    rem Избегаем использования скобок внутри условных операторов
    choice /c YN /m "Would you like to install Node.js LTS automatically via Windows Winget?"
    
    if errorlevel 2 (
        echo [INFO] Installation canceled by user. The application cannot run without Node.js.
        pause
        exit /b
    )
    
    echo.
    echo [INFO] Attempting to install Node.js LTS automatically via Windows Winget...
    winget install -e --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
    
    if %errorlevel% equ 0 (
        echo [SUCCESS] Node.js LTS has been installed successfully!
        echo ====================================================================
        echo [IMPORTANT] Windows needs to reload system environment variables PATH.
        echo [IMPORTANT] Please CLOSE this console window and run start.bat again!
        echo ====================================================================
        pause
        exit
    ) else (
        echo [ERROR] Automatic installation via winget failed.
        echo [ERROR] Please install Node.js manually from: https://nodejs.org/
        pause
        exit /b
    )
)

:: 2. ПРОВЕРКА И НАСТРОЙКА PYTHON VENV
if not exist "backend\venv" (
    echo [INFO] Python virtual environment not found.
    echo [INFO] Creating virtual environment...
    python -m venv backend\venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. 
        echo [ERROR] Please make sure Python is installed and added to your system PATH.
        pause
        exit /b
    )
    
    echo [INFO] Activating virtual environment...
    call backend\venv\Scripts\activate
    
    echo [INFO] Upgrading pip...
    python -m pip install --upgrade pip
    
    echo [INFO] Installing Python dependencies from requirements.txt...
    if exist "backend\requirements.txt" (
        pip install -r backend\requirements.txt
    ) else (
        echo [WARNING] requirements.txt not found. Installing core packages manually...
        pip install websockets keyboard mss pywin32 opencv-python numpy rapidocr-onnxruntime requests
    )
    echo [SUCCESS] Python environment is set up successfully!
) else (
    echo [INFO] Python virtual environment detected. Activating...
    call backend\venv\Scripts\activate
)

:: 3. ПРОВЕРКА И НАСТРОЙКА ELECTRON (node_modules)
if not exist "frontend\node_modules" (
    echo [INFO] Node.js dependencies not found.
    echo [INFO] Installing Electron and frontend packages...
    cd frontend
    call npm install
    cd ..
    echo [SUCCESS] Electron dependencies installed successfully!
)

echo ==================================================
echo   LAUNCHING APPLICATION...
echo ==================================================

:: Запуск Python бэкенда в фоне
start /B "SC_Backend" python backend/main.py

:: Переход в папку фронтенда и запуск Electron
cd frontend
npm start

:: Когда Electron закроется, тихо закрываем за собой Python-процесс
echo [INFO] Closing background processes...
taskkill /F /IM python.exe /T >nul 2>&1
exit