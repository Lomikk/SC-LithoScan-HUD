const { app, BrowserWindow, ipcMain, screen, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec } = require('child_process');

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

    if (!fs.existsSync(backendPath)) {
        dialog.showErrorBox("Ошибка запуска", "Файл бэкенда не найден:\n" + backendPath);
        return;
    }

    backendProcess = spawn(backendPath, [], {
        detached: false, 
        windowsHide: true,
        cwd: path.dirname(backendPath),
        stdio: ['ignore', 'pipe', 'pipe'] 
    });

    // ЕДИНСТВЕННЫЙ обработчик stdout
    backendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`[Backend]: ${output.trim()}`);
        
        if (output.includes("===BACKEND_READY===") && !windowCreated) {
            console.log("Бэкенд готов! Открываем окно.");
            windowCreated = true;
            createWindow();
        }
    });

    // ЕДИНСТВЕННЫЙ обработчик stderr
    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend Error]: ${data.toString().trim()}`);
    });

    backendProcess.on('error', (err) => {
        dialog.showErrorBox("Ошибка запуска бэкенда", `Не удалось запустить процесс Питона:\n${err.message}`);
    });

    backendProcess.on('exit', (code) => {
        if (code !== 0 && code !== null) {
            dialog.showErrorBox("Критическая ошибка бэкенда", `Процесс Python неожиданно завершился (код ${code}).\nУбедитесь, что антивирус не удалил файл.`);
        }
    });
}

// ==========================================
// 2. СОЗДАНИЕ ОКНА
// ==========================================
function createWindow() {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    mainWindow = new BrowserWindow({
        title: "LithoScan HUD",
        width: width,
        height: height,
        x: 0,
        y: 0,
        transparent: true,      
        frame: false,           
        alwaysOnTop: true,      
        skipTaskbar: false,     
        resizable: false,       
//        type: 'toolbar',        
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);

    mainWindow.on('blur', () => {
        mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);
    });

    mainWindow.setIgnoreMouseEvents(false);
    mainWindow.loadFile('app/index.html');

    // ВОЗВРАЩАЕМ ЗАЩИТУ ОТ СМЕЩЕНИЯ МАСШТАБА (СЛУЧАЙНО УДАЛЕННУЮ РАНЕЕ)
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.setZoomFactor(1.0);
    });
}

// ==========================================
// 3. ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ
// ==========================================
app.whenReady().then(() => {
    
    if (app.isPackaged) {
        startBackend(); 
        
        setTimeout(() => {
            if (!windowCreated) {
                console.log("Аварийный тайм-аут: бэкенд не ответил вовремя. Открываем принудительно.");
                windowCreated = true;
                createWindow();
            }
        }, 5000);
    } else {
        console.log("Режим разработки: Бэкенд запущен внешним скриптом.");
        windowCreated = true;
        createWindow();
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;
    win.setIgnoreMouseEvents(ignore, { forward: true });
});

// ФУНКЦИЯ УНИЧТОЖЕНИЯ БЭКЕНДА
function killBackend() {
    if (backendProcess && backendProcess.pid) {
        console.log(`Завершаем процесс бэкенда (PID: ${backendProcess.pid})...`);
        exec(`taskkill /pid ${backendProcess.pid} /T /F`, (err) => {
            if (err) {
                console.log("Taskkill завершился с ошибкой, пробуем стандартный kill()");
                backendProcess.kill(); 
            } else {
                console.log("Бэкенд успешно выгружен.");
            }
        });
    }
}

app.on('will-quit', () => {
    killBackend();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});