const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    // Получаем размеры основного монитора
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    mainWindow = new BrowserWindow({
        width: width,
        height: height,
        x: 0,
        y: 0,
        transparent: true,      // Идеальная прозрачность для оверлея
        frame: false,           // Без рамок
        alwaysOnTop: true,      // Поверх всех окон (поверх игры)
        skipTaskbar: false,      // Скрыть из панели задач
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
    // mainWindow.webContents.openDevTools({ mode: 'detach' });
}

app.whenReady().then(() => {
    createWindow();
    
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

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});