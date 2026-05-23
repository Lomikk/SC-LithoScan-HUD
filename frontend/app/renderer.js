let ws;
let currentConfigs = { method: 'Dinyx Solventation', system: 'ALL', yieldSys: 'ALL' };

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => setStatus("CONNECTED TO BACKEND", "#00FF00");

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
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
            case 'scan_frame':
                UI.flashScanFrame(data.t, data.l, data.w, data.h);
                break;
            case 'scan_totals':
                UI.updateTotals(data); // Передаем чистый JSON в UI
                break;
            case 'scan_table_data':
                UI.updateTable(data.data); // Строим HTML из JSON массива
                break;
        }
    };

    ws.onclose = () => {
        setStatus("CONNECTION LOST. RECONNECTING...", "#FF0000");
        setTimeout(connectWebSocket, 2000);
    };
}

connectWebSocket();

// ============================================================================
// ВЗАИМОДЕЙСТВИЕ С ИНТЕРФЕЙСОМ И ОТПРАВКА КОНФИГА
// ============================================================================
function setStatus(text, color) {
    const el = document.getElementById('ui-status');
    el.innerText = text; el.style.color = color || 'var(--text-dim)';
}

function setUIEditMode(isEdit) {
    document.getElementById('edit-mode-warning').style.display = isEdit ? 'block' : 'none';
    window.api.setIgnoreMouseEvents(!isEdit); // Переключаем клик-сквозь ОС
}

function sendConfigUpdate() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: "update_config",
            method: currentConfigs.method,
            system: currentConfigs.system,
            yield_system: currentConfigs.yieldSys
        }));
    }
}

// Управление выпадающими списками (Dropdowns)
function toggleDropdown(e, id) {
    e.stopPropagation(); 
    document.querySelectorAll('.select-options').forEach(el => {
        if(el.id !== 'opts-' + id) el.classList.remove('show');
    });
    document.getElementById('opts-' + id).classList.toggle('show');
}

function selectOpt(e, type, value, label) {
    e.stopPropagation(); 
    let safeType = type === 'yield' ? 'yieldSys' : type;
    currentConfigs[safeType] = value;
    
    let prefix = type === 'method' ? "Method: " : (type === 'system' ? "Prices: " : "Bonuses: ");
    document.getElementById('val-' + type).innerText = prefix + label;
    document.getElementById('opts-' + type).classList.remove('show');
    
    sendConfigUpdate();
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

// Привязка чекбоксов (Обновление состояния uiState)
window.toggleUI = function(className) {
    if(className === '.ui-ref-data') uiState.showRef = !uiState.showRef;
    if(className === '.ui-raw-data') uiState.showRaw = !uiState.showRaw;
    if(className === '.ui-col-comp') uiState.cols.comp = !uiState.cols.comp;
    if(className === '.ui-col-scu') uiState.cols.scu = !uiState.cols.scu;
    if(className === '.ui-col-dens') uiState.cols.dens = !uiState.cols.dens;
    if(className === '.ui-col-val') uiState.cols.val = !uiState.cols.val;
    if(className === '.ui-col-mods') uiState.cols.mods = !uiState.cols.mods;
    UI.applyFormatting();
};
window.toggleLayout = function() { uiState.isInline = !uiState.isInline; UI.applyFormatting(); };
window.toggleFormat = function() { uiState.shortNums = !uiState.shortNums; UI.applyFormatting(); };
window.toggleMinerals = function() { uiState.shortMins = !uiState.shortMins; UI.applyFormatting(); };