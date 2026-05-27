let ws;

// ============================================================================
// 1. МЕНЕДЖЕР НАСТРОЕК (LOCAL STORAGE)
// ============================================================================
const DEFAULT_SETTINGS = {
    method: 'Dinyx Solventation',
    system: 'ALL',
    yieldSys: 'ALL',
    theme: 'glass',
    ui: {
        showRef: true, showRaw: true, isInline: false,
        shortNums: true, shortMins: false,
        cols: { comp: true, scu: true, dens: true, val: true, mods: true }
    }
};

// Единый центр управления темами. Добавляй новые темы только сюда!
// Единый центр управления темами. Добавляй новые темы только сюда!
const AVAILABLE_THEMES = {
    'glass':      { title: 'GLASS HUD',   desc: '(Holographic)' },
    'classic':    { title: 'CLASSIC HUD', desc: '(Cyan/Green)' },
    'amber':      { title: 'AMBER HUD',   desc: '(Orange)' },
    'outlaw':     { title: 'OUTLAW HUD',  desc: '(GrimHEX Red)' },
    'industrial': { title: 'INDUSTRIAL',  desc: '(Drake Yellow)' },
    'synthwave':  { title: 'SYNTHWAVE',   desc: '(MicroTech Pink)' },
    'luxury':     { title: 'LUXURY HUD',  desc: '(Origin White)' }
};

// Загружаем из памяти или создаем новый профиль
window.appSettings = JSON.parse(localStorage.getItem('minerSettings')) || JSON.parse(JSON.stringify(DEFAULT_SETTINGS));

function saveSettings() {
    localStorage.setItem('minerSettings', JSON.stringify(window.appSettings));
}

function applySettingsToUI() {
    // 1. Применяем тему
    document.body.setAttribute('data-theme', window.appSettings.theme);
    
    // 2. Обновляем текст в выпадающих списках (Dropdowns)
    document.getElementById('val-method').innerText = "Method: " + window.appSettings.method;
    
    const sysLabels = { 'ALL': 'ALL SYSTEMS', 'Stanton': 'STANTON', 'Pyro': 'PYRO', 'Nyx': 'NYX' };
    document.getElementById('val-system').innerText = "Prices: " + sysLabels[window.appSettings.system];
    document.getElementById('val-yield').innerText = "Bonuses: " + sysLabels[window.appSettings.yieldSys];
    
    // Берем короткое название темы из нашего единого словаря
    const activeTheme = AVAILABLE_THEMES[window.appSettings.theme] || AVAILABLE_THEMES['glass'];
    document.getElementById('val-theme').innerText = "Theme: " + activeTheme.title;

    // 3. Обновляем галочки у чекбоксов
    document.getElementById('cb-showRef').checked = window.appSettings.ui.showRef;
    document.getElementById('cb-showRaw').checked = window.appSettings.ui.showRaw;
    document.getElementById('cb-isInline').checked = window.appSettings.ui.isInline;
    document.getElementById('cb-shortNums').checked = window.appSettings.ui.shortNums;
    document.getElementById('cb-shortMins').checked = window.appSettings.ui.shortMins;
    
    document.getElementById('cb-col-comp').checked = window.appSettings.ui.cols.comp;
    document.getElementById('cb-col-scu').checked = window.appSettings.ui.cols.scu;
    document.getElementById('cb-col-dens').checked = window.appSettings.ui.cols.dens;
    document.getElementById('cb-col-val').checked = window.appSettings.ui.cols.val;
    document.getElementById('cb-col-mods').checked = window.appSettings.ui.cols.mods;
    
    // 4. Даем команду UI.js перерисовать таблицу согласно новым настройкам
    if (typeof UI !== 'undefined') UI.applyFormatting();
}

// Запускается по кнопке "Reset to Factory Settings"
window.resetFactorySettings = function() {
    localStorage.removeItem('minerSettings');
    window.appSettings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    applySettingsToUI();
    sendConfigUpdate();
}

// ============================================================================
// 2. СЕТЬ (WEBSOCKET)
// ============================================================================
function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
        setStatus("CONNECTED TO BACKEND", "var(--color-ref)");
        // При подключении сразу отправляем Питону наши сохраненные настройки
        sendConfigUpdate(); 
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'init':
                populateMethods(data.methods);
                setUIEditMode(data.is_edit);
                break;
            case 'init':
                populateMethods(data.methods);
                setUIEditMode(data.is_edit);
                break;
            case 'status':
                setStatus(data.text, data.color);
                break;
            case 'edit_mode':
                setUIEditMode(data.is_edit);
                break;
            case 'visibility': 
                document.querySelector('.scene').style.display = data.show ? 'block' : 'none';
                if (!data.show) document.getElementById('edit-mode-warning').style.display = 'none';
                // else if (!window.appSettings.is_edit) ... (зависит от статуса)
                break;
            case 'scan_frame':
                UI.flashScanFrame(data.t, data.l, data.w, data.h);
                break;
            case 'scan_totals':
                UI.updateTotals(data); 
                break;
            case 'scan_table_data':
                UI.updateTable(data.data); 
                break;
            case 'sig_result':
                UI.updateSignature(data);
                break;
            case 'db_status':
                document.getElementById('ui-db-date').innerText = data.date;
                break;    
        }           
    };

    ws.onclose = () => {
        setStatus("CONNECTION LOST. RECONNECTING...", "#FF0000");
        setTimeout(connectWebSocket, 2000);
    };
}

// ============================================================================
// 3. ОБРАБОТКА ДЕЙСТВИЙ ПОЛЬЗОВАТЕЛЯ
// ============================================================================
function setStatus(text, color) {
    const el = document.getElementById('ui-status');
    el.innerText = text; el.style.color = color || 'var(--text-dim)';
}

function setUIEditMode(isEdit) {
    document.getElementById('edit-mode-warning').style.display = isEdit ? 'block' : 'none';
    window.api.setIgnoreMouseEvents(!isEdit);
}

function sendConfigUpdate() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: "update_config",
            method: window.appSettings.method,
            system: window.appSettings.system,
            yield_system: window.appSettings.yieldSys
        }));
    }
}

window.triggerAction = function(actionName) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: actionName }));
    }
}

// DROPDOWNS
window.toggleDropdown = function(e, id) {
    e.stopPropagation(); 
    document.querySelectorAll('.select-options').forEach(el => {
        if(el.id !== 'opts-' + id) el.classList.remove('show');
    });
    document.getElementById('opts-' + id).classList.toggle('show');
}

window.selectOpt = function(e, type, value, label) {
    e.stopPropagation(); 
    
    if (type === 'theme') {
        window.appSettings.theme = value;
        document.body.setAttribute('data-theme', value);
        document.getElementById('val-theme').innerText = "Theme: " + label;
    } else {
        let safeType = type === 'yield' ? 'yieldSys' : type;
        window.appSettings[safeType] = value;
        
        let prefix = type === 'method' ? "Method: " : (type === 'system' ? "Prices: " : "Bonuses: ");
        document.getElementById('val-' + type).innerText = prefix + label;
        sendConfigUpdate(); // Если изменили метод/систему, отправляем Питону
    }
    
    document.getElementById('opts-' + type).classList.remove('show');
    saveSettings(); // Сохраняем в LocalStorage
}

document.addEventListener('click', () => document.querySelectorAll('.select-options.show').forEach(el => el.classList.remove('show')));

function populateMethods(methodsList) {
    const container = document.getElementById('opts-method');
    container.innerHTML = "";
    methodsList.forEach(m => {
        let div = document.createElement('div');
        div.className = "option-item";
        div.innerText = m;
        div.onclick = (e) => selectOpt(e, 'method', m, m);
        container.appendChild(div);
    });
}

function populateThemes() {
    const container = document.getElementById('opts-theme');
    container.innerHTML = "";
    
    Object.keys(AVAILABLE_THEMES).forEach(themeId => {
        const themeData = AVAILABLE_THEMES[themeId];
        let div = document.createElement('div');
        div.className = "option-item";
        // Пишем полное название в выпадающий список: "GLASS HUD (Holographic)"
        div.innerText = `${themeData.title} ${themeData.desc}`;
        // При клике передаем только короткое имя для шапки: "GLASS HUD"
        div.onclick = (e) => selectOpt(e, 'theme', themeId, themeData.title);
        container.appendChild(div);
    });
}

// ЧЕКБОКСЫ
window.toggleSetting = function(key, isChecked) {
    window.appSettings.ui[key] = isChecked;
    UI.applyFormatting();
    saveSettings();
}

window.toggleCol = function(key, isChecked) {
    window.appSettings.ui.cols[key] = isChecked;
    UI.applyFormatting();
    saveSettings();
}



// Инициализация при старте приложения
populateThemes();
applySettingsToUI();
connectWebSocket();