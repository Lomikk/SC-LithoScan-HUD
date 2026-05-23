const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    setIgnoreMouseEvents: (ignore) => ipcRenderer.send('set-ignore-mouse-events', ignore)
});