// ============================================================================
// 1. EXACT MOCK DATA FROM SCREENSHOTS
// ============================================================================
const mockScans = {
    "img1": {
        meta_vol: 15.49,
        meta_method: "DINYX SOLV",
        meta_bonus: 556.0,
        totals: { t_dens: 23248, r_dens: 3544, t_prof: 360117, r_prof: 54895, opt_dens: 33133, opt_scu: 10.04 },
        minerals: [
            { name: "GOLD", percent: 42.45, grade: 0, scu_ref: 6.81, scu_raw: 6.58, dens_ref: 14900, dens_raw: 1134, prof_ref: 230801, prof_raw: 17570, station: "MIC-L2", system: "Stanton", bonus: 0.09, is_core: true },
            { name: "TARANITE", percent: 22.39, grade: 0, scu_ref: 3.56, scu_raw: 3.47, dens_ref: 6583, dens_raw: 1970, prof_ref: 101972, prof_raw: 30517, station: "Levski", system: "Nyx", bonus: 0.08, is_core: true },
            { name: "QUARTZ", percent: 30.74, grade: 0, scu_ref: 5.02, scu_raw: 4.76, dens_ref: 1765, dens_raw: 439, prof_ref: 27344, prof_raw: 6804, station: "Nyx Gateway", system: "Stanton", bonus: 0.11, is_core: false },
            { name: "INERT", percent: 4.40, grade: 0, scu_ref: 0.65, scu_raw: 0.68, dens_ref: 0, dens_raw: 0, prof_ref: 0, prof_raw: 4, station: "-", system: "Unknown", bonus: 0, is_core: false }
        ]
    },
    "img2": {
        meta_vol: 46.03,
        meta_method: "DINYX SOLV",
        meta_bonus: 9703.7,
        totals: { t_dens: 25021, r_dens: 255, t_prof: 1151702, r_prof: 11748, opt_dens: 51841, opt_scu: 21.33 },
        minerals: [
            { name: "LINDINIUM", percent: 40.28, grade: 260, scu_ref: 18.85, scu_raw: 18.54, dens_ref: 20882, dens_raw: 0, prof_ref: 961187, prof_raw: 0, station: "MIC-L5", system: "Stanton", bonus: 0.07, is_core: true },
            { name: "LINDINIUM", percent: 6.05, grade: 897, scu_ref: 2.83, scu_raw: 2.78, dens_ref: 3136, dens_raw: 0, prof_ref: 144369, prof_raw: 0, station: "MIC-L5", system: "Stanton", bonus: 0.07, is_core: true },
            { name: "TUNGSTEN", percent: 8.15, grade: 428, scu_ref: 3.88, scu_raw: 3.75, dens_ref: 1003, dens_raw: 252, prof_ref: 46151, prof_raw: 11622, station: "MIC-L2", system: "Stanton", bonus: 0.09, is_core: false },
            { name: "INERT", percent: 45.51, grade: 0, scu_ref: 19.90, scu_raw: 20.95, dens_ref: 0, dens_raw: 3, prof_ref: -5, prof_raw: 126, station: "-", system: "Unknown", bonus: 0, is_core: false }
        ]
    }
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
// DRAG & DROP & ANIMATION LOGIC
// ============================================================================
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }, false);
});

dropZone.addEventListener('drop', e => handleFiles(e.dataTransfer.files), false);
fileInput.addEventListener('change', function() { handleFiles(this.files); });

function handleFiles(files) {
    if (files.length === 0) return;
    const file = files[0];
    
    const dropText = document.getElementById('drop-text');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const loaderLogs = document.getElementById('loader-logs');
    const calcApp = document.getElementById('calc-app');
    
    // Возврат в состояние сканирования
    calcApp.classList.add('empty-state');
    document.getElementById('scan-complete-overlay').classList.add('hide');
    document.getElementById('scan-laser').classList.remove('hide');
    
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewImage.style.opacity = "0.3"; 
        
        dropText.classList.add('hide');
        previewContainer.classList.remove('hide');
        loaderLogs.classList.remove('hide');
        
        document.getElementById('log-2').classList.add('hide');
        document.getElementById('log-4').classList.add('hide');
        
        setTimeout(() => document.getElementById('log-2').classList.remove('hide'), 600);
        setTimeout(() => {
            document.getElementById('log-4').classList.remove('hide');
            
            setTimeout(() => {
                const nameLower = file.name.toLowerCase();
                renderResults(nameLower.includes("img2") ? mockScans["img2"] : mockScans["img1"]);
                
                calcApp.classList.remove('empty-state');
                loaderLogs.classList.add('hide');
                document.getElementById('scan-laser').classList.add('hide');
                previewImage.style.opacity = "0.8"; 
                document.getElementById('scan-complete-overlay').classList.remove('hide');
                
            }, 800);
        }, 1600);
    };
    reader.readAsDataURL(file);
}