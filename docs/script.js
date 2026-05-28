// ============================================================================
// 1. EXACT MOCK DATA FROM SCREENSHOT (Image1.png)
// ============================================================================
const scanData = {
    meta_vol: 17.50,
    meta_method: "DINYX SOLV",
    meta_bonus: 630.0,
    totals: {
        t_dens: 23791,
        r_dens: 3259,
        t_prof: 416348,
        r_prof: 57037,
        opt_dens: 35825,
        opt_scu: 11.62
    },
    minerals: [
        { name: "BEXALITE", percent: 53.35, grade: 302, scu_ref: 9.93, scu_raw: 9.34, dens_ref: 19189, dens_raw: 2785, prof_ref: 335799, prof_raw: 48735, station: "MIC-L5", system: "Stanton", bonus: 0.12, is_core: true },
        { name: "BEXALITE", percent: 6.35, grade: 582, scu_ref: 1.18, scu_raw: 1.11, dens_ref: 2284, dens_raw: 331, prof_ref: 39969, prof_raw: 5801, station: "MIC-L5", system: "Stanton", bonus: 0.12, is_core: true },
        { name: "BORASE", percent: 3.65, grade: 421, scu_ref: 0.66, scu_raw: 0.64, dens_ref: 1245, dens_raw: 59, prof_ref: 21786, prof_raw: 1035, station: "MIC-L5", system: "Stanton", bonus: 0.09, is_core: true },
        { name: "GOLD", percent: 3.06, grade: 491, scu_ref: 0.55, scu_raw: 0.54, dens_ref: 1074, dens_raw: 82, prof_ref: 18796, prof_raw: 1431, station: "MIC-L2", system: "Stanton", bonus: 0.09, is_core: true },
        { name: "INERT", percent: 33.57, grade: 0, scu_ref: 5.58, scu_raw: 5.87, dens_ref: 0, dens_raw: 2, prof_ref: -1, prof_raw: 35, station: "-", system: "Unknown", bonus: 0, is_core: false }
    ]
};

const MINERAL_COLORS = {
    "QUANTANIUM": { short: "QUAN", color: "#F700FF" }, "GOLD": { short: "GOLD", color: "#A3AA40" },
    "TARANITE": { short: "TARA", color: "#BCA32F" }, "TUNGSTEN": { short: "TUNG", color: "#D49D1E" },
    "HEPHAESTANITE": { short: "HEPH", color: "#DC9639" }, "QUARTZ": { short: "QUAR", color: "#D49746" },
    "SILICON": { short: "SILI", color: "#A69D91" }, "INERT": { short: "INER", color: "#9E9E9E" },
    "LINDINIUM": { short: "LIND", color: "#F700FF" }
};

function getMineralInfo(name) {
    let upName = name.toUpperCase();
    if (upName === "INERT MATERIALS") upName = "INERT";
    return MINERAL_COLORS[upName] || { short: upName.substring(0, 4), color: "#FFFFFF" };
}

function formatFullNum(num) { return (Math.round(num) + 0).toLocaleString('en-US'); }

function getGradeInfo(grade) {
    if (grade < 300) return { text: "grade-trash", row: "" };
    if (grade < 500) return { text: "grade-base", row: "" };
    if (grade < 700) return { text: "grade-uncommon", row: "" };
    if (grade < 850) return { text: "grade-rare", row: "" };
    if (grade < 950) return { text: "grade-epic", row: "row-glow-epic" };
    return { text: "grade-legendary", row: "row-glow-legendary" };
}

function renderResults(data) {
    document.getElementById('meta-vol').innerText = `VOL: ${data.meta_vol.toFixed(2)} SCU`;
    document.getElementById('meta-method').innerText = `METHOD: ${data.meta_method}`;
    document.getElementById('meta-bonus').innerText = `BONUS: +${data.meta_bonus.toFixed(1)}%`;
    
    document.getElementById('t-dens-full').innerText = formatFullNum(data.totals.t_dens);
    document.getElementById('r-dens-full').innerText = formatFullNum(data.totals.r_dens);
    document.getElementById('t-prof-full').innerText = formatFullNum(data.totals.t_prof);
    document.getElementById('r-prof-full').innerText = formatFullNum(data.totals.r_prof);
    
    document.getElementById('opt-dens').innerText = formatFullNum(data.totals.opt_dens);
    document.getElementById('opt-scu').innerText = data.totals.opt_scu.toFixed(2);

    const verdictEl = document.getElementById('scan-verdict');
    let vText = "SKIP IT", vClass = "verdict-skip";
    
    if (data.totals.opt_dens >= 30000) { 
        vText = "JACKPOT"; vClass = "verdict-jackpot";
    } else if (data.totals.opt_dens >= 20000) { 
        vText = "GOOD YIELD"; vClass = "verdict-good";
    } else if (data.totals.opt_dens >= 12000) { 
        vText = "AVERAGE"; vClass = "verdict-average";
    }
    
    verdictEl.innerText = vText; 
    verdictEl.className = `verdict-base ${vClass}`;

    let html = "";
    data.minerals.forEach(chunk => {
        const minInfo = getMineralInfo(chunk.name);
        const gInfo = getGradeInfo(chunk.grade);
        const coreClass = chunk.is_core ? "row-core" : "row-trash";
        const opacityClass = minInfo.short === "INER" ? "opacity-dim" : "";
        
        let modText = "-";
        if (chunk.bonus > 0) {
            let sysClass = "sys-default"; 
            if (chunk.system === "Stanton") sysClass = "sys-stanton";
            else if (chunk.system === "Pyro") sysClass = "sys-pyro";
            else if (chunk.system === "Nyx") sysClass = "sys-nyx";
            
            modText = `<span class="${sysClass}">${chunk.station}</span> (+${(chunk.bonus * 100).toFixed(0)}%)`;
        }

        html += `
        <tr class="${gInfo.row} ${coreClass} ${opacityClass}">
            <td class="cell ui-col-mineral">
                <div class="layout-container align-items-baseline">
                    <span class="mineral-name" style="color: ${minInfo.color}; text-shadow: 0 0 5px ${minInfo.color};">${minInfo.short === 'INER' ? 'INERT' : chunk.name.toUpperCase()}</span>
                    <span class="grade ${gInfo.text}">[${chunk.grade}]</span>
                </div>
            </td>
            <td class="cell ui-col-comp">
                <b>${chunk.percent.toFixed(2)}%</b>
                <div class="bar-bg"><div class="bar-fill" style="background: ${minInfo.color}; width: ${Math.min(100, chunk.percent)}%; box-shadow: 0 0 5px ${minInfo.color};"></div></div>
            </td>
            <td class="cell ui-col-scu">
                <div class="layout-container">
                    <span class="v-ref">${chunk.scu_ref.toFixed(2)}</span>
                    <span class="v-raw">${chunk.scu_raw.toFixed(2)}</span>
                </div>
            </td>
            <td class="cell ui-col-dens">
                <div class="layout-container">
                    <span class="v-ref">${formatFullNum(chunk.dens_ref)}</span>
                    <span class="v-raw">${formatFullNum(chunk.dens_raw)}</span>
                </div>
            </td>
            <td class="cell ui-col-val text-right">
                <div class="layout-container align-end">
                    <span class="v-ref">${formatFullNum(chunk.prof_ref)}</span>
                    <span class="v-raw">${formatFullNum(chunk.prof_raw)}</span>
                </div>
            </td>
            <td class="cell ui-col-mods"><span class="mod-text">${modText}</span></td>
        </tr>`;
    });

    document.getElementById('minerals-body').innerHTML = html;
}

document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        const theme = e.target.getAttribute('data-target');
        document.getElementById('calc-app').setAttribute('data-theme', theme);
    });
});

// ============================================================================
// УМНАЯ ГЕНЕРАЦИЯ ТИКЕРОВ (ПО БОКАМ) - ИДЕАЛЬНО ПЛАВНАЯ
// ============================================================================
function generateTickers() {
    const panelLeft = document.getElementById('panel-left');
    const panelRight = document.getElementById('panel-right');
    if(!panelLeft || !panelRight) return;
    
    panelLeft.innerHTML = '';
    panelRight.innerHTML = '';

    if (window.innerWidth < 1250) return;

    const minKeys = Object.keys(MINERAL_COLORS);
    
    // 1. ИСПРАВЛЕНИЕ ОБРЕЗАННЫХ КРАЕВ
    const trackWidth = 110; // Ширина одной колонки
    const availableSpace = (window.innerWidth - 1200) / 2; // Свободное место с одной стороны
    // Используем Math.floor (округление вниз), чтобы рисовать только ЦЕЛЫЕ колонки
    const tracksCount = Math.max(0, Math.floor(availableSpace / trackWidth));

    // 2. ИСПРАВЛЕНИЕ ДЕРГАЮЩЕЙСЯ АНИМАЦИИ (Точная математика пикселей)
    const itemsPerTrack = 50; // УВЕЛИЧИЛИ ДО 50! (Хватит даже на 4K экраны)
    const itemHeight = 47; 
    const shiftHeight = itemsPerTrack * itemHeight; // Скрипт сам пересчитает сдвиг (теперь это 2350px)

    function createTrack(isUp) {
        let html = "";
        for(let i=0; i<itemsPerTrack; i++) {
            const randomMin = minKeys[Math.floor(Math.random() * minKeys.length)];
            const info = MINERAL_COLORS[randomMin];
            const fakePrice = (Math.random() * (8.5 - 0.5) + 0.5).toFixed(1) + "k";
            const trendUp = Math.random() > 0.5;
            const trendClass = trendUp ? "up" : "down";
            const trendIcon = trendUp ? "▲" : "▼";

            html += `
                <div class="ticker-item-wrap">
                    <div class="ticker-item" style="border-color: ${info.color}40;">
                        <span class="ticker-name" style="color: ${info.color};">${info.short}</span>
                        <span class="ticker-val ${trendClass}">${trendIcon} ${fakePrice}</span>
                    </div>
                </div>`;
        }
        
        const track = document.createElement('div');
        const duration = Math.floor(Math.random() * 50 + 80);
        track.className = `ticker-track ${isUp ? 'ticker-up' : 'ticker-down'}`;
        track.style.animationDuration = `${duration}s`;
        
        // ПЕРЕДАЕМ ТОЧНЫЕ ПИКСЕЛИ В CSS!
        track.style.setProperty('--shift-height', `-${shiftHeight}px`);
        
        track.innerHTML = html + html; 
        return track;
    }

    for(let i=0; i<tracksCount; i++) {
        panelLeft.appendChild(createTrack(true));   
        panelRight.appendChild(createTrack(false)); 
    }
}

window.addEventListener('resize', () => {
    clearTimeout(window.tickerTimeout);
    window.tickerTimeout = setTimeout(generateTickers, 300);
});
document.addEventListener("DOMContentLoaded", generateTickers);

// Пересчитываем тикеры при изменении размера окна
window.addEventListener('resize', () => {
    clearTimeout(window.tickerTimeout);
    window.tickerTimeout = setTimeout(generateTickers, 300);
});
document.addEventListener("DOMContentLoaded", generateTickers);

// ============================================================================
// ИНТЕРАКТИВНЫЙ КЛИК ПО СКРИНШОТУ
// ============================================================================
const demoTrigger = document.getElementById('demo-trigger');
let isScanning = false;
let isScanComplete = false;

demoTrigger.addEventListener('click', function() {
    if (isScanning) return; // Блокируем клики во время анимации

    const clickPrompt = document.getElementById('click-prompt');
    const targetBox = document.getElementById('scan-target-box');
    const loaderLogs = document.getElementById('loader-logs');
    const calcApp = document.getElementById('calc-app');
    const completeOverlay = document.getElementById('scan-complete-overlay');
    const gameBg = document.getElementById('game-bg');

    // Если скан уже был завершен - сбрасываем всё в начало
    if (isScanComplete) {
        calcApp.classList.add('empty-state');
        completeOverlay.classList.add('hide');
        clickPrompt.classList.remove('hide');
        gameBg.style.opacity = "0.6";
        isScanComplete = false;
        return;
    }

    // --- НАЧАЛО СКАНИРОВАНИЯ ---
    isScanning = true;
    
    // Прячем кнопку, показываем рамку сканера и логи
    clickPrompt.classList.add('hide');
    targetBox.classList.remove('hide');
    loaderLogs.classList.remove('hide');
    gameBg.style.opacity = "0.4"; // Затемняем фон для фокуса на сканере
    
    // Сброс логов
    document.getElementById('log-2').classList.add('hide');
    document.getElementById('log-4').classList.add('hide');
    
    // Анимация текста в логах
    setTimeout(() => document.getElementById('log-2').classList.remove('hide'), 600);
    
    setTimeout(() => {
        document.getElementById('log-4').classList.remove('hide');
        
        // --- ЗАВЕРШЕНИЕ СКАНИРОВАНИЯ ---
        setTimeout(() => {
            // Отрисовываем данные
            renderResults(scanData);
            
            // Проявляем калькулятор
            calcApp.classList.remove('empty-state');
            
            // Скрываем сканер, показываем надпись Complete
            targetBox.classList.add('hide');
            loaderLogs.classList.add('hide');
            completeOverlay.classList.remove('hide');
            gameBg.style.opacity = "0.2"; // Сильно затемняем скриншот, фокус на калькуляторе
            
            isScanning = false;
            isScanComplete = true;
        }, 800);
    }, 1600);
});