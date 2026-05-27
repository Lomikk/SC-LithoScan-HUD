const { exec } = require('child_process'); // Добавь этот импорт в самый верх, если его там нет
const { app, BrowserWindow, ipcMain, screen, dialog } = require('electron'); // <-- добавили dialog
const path = require('path');
const fs = require('fs'); // <-- добавили fs
const { spawn } = require('child_process');

let mainWindow;
let backendProcess = null;
let windowCreated = false;

// ==========================================
// 1. ЗАПУСК БЭКЕНДА (PYTHON .EXE)
// ==========================================
function startBackend() {
    const backendPath = app.isPackaged 
        ? path.join(process.resourcesPath, 'backend-bin', 'lithoscan_backend.exe')
        : path.join(__dirname, 'backend-bin', 'lithoscan_backend.exe');

    console.log("Запускаем бэкенд по пути:", backendPath);

    // Проверяем, на месте ли файл
    if (!fs.existsSync(backendPath)) {
        dialog.showErrorBox("Ошибка запуска", "Файл бэкенда не найден:\n" + backendPath);
        return;
    }

    // Запускаем процесс напрямую, БЕЗ shell: true [2.4]
   backendProcess = spawn(backendPath, [], {
        detached: false, 
        windowsHide: true,
        cwd: path.dirname(backendPath),
        env: { ...process.env, PYTHONUTF8: "1" },
        stdio: ['ignore', 'pipe', 'pipe'] // Настраиваем каналы вывода [2.4]
    });

    // Следим за выводом бэкенда в поисках сигнала готовности [2.4]
    backendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`[Backend]: ${output}`);
        
        // Как только питон отрапортовал о готовности — открываем интерфейс! [2.4]
        if (output.includes("===BACKEND_READY===") && !windowCreated) {
            console.log("Бэкенд готов! Открываем окно.");
            windowCreated = true;
            createWindow();
        }
    });

    backendProcess.on('error', (err) => {
        dialog.showErrorBox(
            "Ошибка запуска бэкенда", 
            `Не удалось запустить процесс Питона:\n${err.message}`
        );
    });

    backendProcess.on('exit', (code) => {
        if (code !== 0 && code !== null) {
            dialog.showErrorBox(
                "Критическая ошибка бэкенда", 
                `Процесс Python неожиданно завершился (код ${code}).\nУбедитесь, что у программы есть права Администратора.`
            );
        }
    });

    backendProcess.stdout.on('data', (data) => console.log(`[Backend]: ${data}`));
    backendProcess.stderr.on('data', (data) => console.error(`[Backend Error]: ${data}`));
}

// ==========================================
// 2. СОЗДАНИЕ ОКНА
// ==========================================
// ... (здесь идет функция createWindow и остальной код без изменений) ...
// ==========================================
// 2. СОЗДАНИЕ ОКНА
// ==========================================
function createWindow() {
    // Получаем размеры основного монитора
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    mainWindow = new BrowserWindow({
        title: "LithoScan HUD",
        width: width,
        height: height,
        x: 0,
        y: 0,
        transparent: true,      // Идеальная прозрачность для оверлея
        frame: false,           // Без рамок
        alwaysOnTop: true,      // Поверх всех окон (поверх игры)
        skipTaskbar: false,      // Скрыть из панели задач
        resizable: false,
        //type: 'toolbar',        // <--- 1. Запрещает окну сворачиваться
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    // <--- 2. Форсируем максимальный Z-index поверх игр
    mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);

    // <--- 3. Если игра забирает фокус, жестко держим оверлей наверху
    mainWindow.on('blur', () => {
        mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);
    });

    // Отключаем аппаратное ускорение, если оно конфликтует со Star Citizen
    // app.disableHardwareAcceleration();

    mainWindow.setIgnoreMouseEvents(false);
    mainWindow.loadFile('app/index.html');

    // Раскомментируй для отладки
    // mainWindow.webContents.openDevTools({ mode: 'detach' });
}

// ==========================================
// 3. ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ
// ==========================================
app.whenReady().then(() => {
    startBackend(); 
    
    // Аварийный тайм-аут: если бэкенд не ответил за 5 секунд,
    // всё равно открываем окно, чтобы пользователь не видел вечную загрузку
    setTimeout(() => {
        if (!windowCreated) {
            console.log("Аварийный тайм-аут: бэкенд не ответил вовремя. Открываем принудительно.");
            windowCreated = true;
            createWindow();
        }
    }, 5000);
    
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

// Умный клик-сквозь. Команды приходят из renderer.js
ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;
    
    // forward: true позволяет оверлею ловить mousemove для 3D эффектов, 
    // но клики пролетают насквозь в игру!
    win.setIgnoreMouseEvents(ignore, { forward: true });
});

// УБИВАЕМ БЭКЕНД ПРИ ЗАКРЫТИИ ПРОГРАММЫ
// В самом конце файла frontend/main.js:

// Функция для железного убийства дерева процессов в Windows
function killBackend() {
    if (backendProcess && backendProcess.pid) {
        console.log(`Завершаем процесс бэкенда (PID: ${backendProcess.pid})...`);
        
        // /F - принудительно, /T - убивает дерево процессов (все дочерние потоки Питона)
        exec(`taskkill /pid ${backendProcess.pid} /T /F`, (err) => {
            if (err) {
                console.log("Taskkill завершился с ошибкой, пробуем стандартный kill()");
                backendProcess.kill(); // Резервный откат
            } else {
                console.log("Бэкенд успешно и полностью выгружен из ОЗУ.");
            }
        });
    }
}

// Заменяем will-quit
app.on('will-quit', () => {
    killBackend();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});