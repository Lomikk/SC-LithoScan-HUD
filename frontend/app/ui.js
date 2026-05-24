// ============================================================================
// КОНСТАНТЫ И ФОРМАТИРОВАНИЕ
// ============================================================================
const MINERAL_COLORS = {
    "QUANTANIUM": { short: "QUAN", color: "#F700FF" },
    "STILBITE": { short: "STIL", color: "#F700FF" },
    "SAVR": { short: "SAVR", color: "#F700FF" },
    "RICCITE": { short: "RICC", color: "#F700FF" },
    "LINDINIUM": { short: "LIND", color: "#F700FF" },
    "BORASE": { short: "BORS", color: "#97AE48" },
    "GOLD": { short: "GOLD", color: "#A3AA40" },
    "BEXALITE": { short: "BEX", color: "#AFA737" },
    "TARANITE": { short: "TARA", color: "#BCA32F" },
    "BERLITE": { short: "BERL", color: "#C8A026" },
    "TUNGSTEN": { short: "TUNG", color: "#D49D1E" },
    "AGRICIUM": { short: "AGRI", color: "#E09915" },
    "TITANIUM": { short: "TITA", color: "#ED960D" },
    "LARANITE": { short: "LARA", color: "#FB9206" },
    "DIAMOND": { short: "DIAM", color: "#F39313" },
    "TORBENITE": { short: "TORI", color: "#EC9420" },
    "ICE": { short: "ICE", color: "#E4952C" },
    "HEPHAESTANITE": { short: "HEPH", color: "#DC9639" },
    "QUARTZ": { short: "QUAR", color: "#D49746" },
    "COPPER": { short: "COPP", color: "#CD9852" },
    "ALUMINUM": { short: "ALUM", color: "#C5995F" },
    "TIN": { short: "TIN", color: "#BD9A6B" },
    "CORUNDUM": { short: "CORU", color: "#B59B78" },
    "IRON": { short: "IRON", color: "#AE9C85" },
    "SILICON": { short: "SILI", color: "#A69D91" },
    "INERT": { short: "INER", color: "#9E9E9E" }
};

function getMineralInfo(name) {
    let upName = name.toUpperCase();
    if (upName === "INERT MATERIALS") upName = "INERT";
    return MINERAL_COLORS[upName] || { short: upName.substring(0, 4), color: "#FFFFFF" };
}

function formatFullNum(num) {
    return (Math.round(num) + 0).toLocaleString('en-US');
}

function shortenNum(num) {
    if (Math.abs(num) >= 1000000) return (num / 1000000).toFixed(2) + "M";
    if (Math.abs(num) >= 1000) return (num / 1000).toFixed(1) + "k";
    return Math.round(num).toString();
}

function getGradeInfo(grade) {
    if (grade < 300) return { text: "grade-trash", row: "" };
    if (grade < 500) return { text: "grade-base", row: "" };
    if (grade < 700) return { text: "grade-uncommon", row: "" };
    if (grade < 850) return { text: "grade-rare", row: "" };
    if (grade < 950) return { text: "grade-epic", row: "row-glow-epic" };
    return { text: "grade-legendary", row: "row-glow-legendary" };
}

// ============================================================================
// ГЕНЕРАЦИЯ HTML
// ============================================================================
const UI = {
    updateTotals: function(data) {
        document.getElementById('meta-vol').innerText = `VOL: ${data.meta_vol.toFixed(2)} SCU`;
        document.getElementById('meta-method').innerText = `METHOD: ${data.meta_method}`;
        document.getElementById('meta-bonus').innerText = `BONUS: +${data.meta_bonus.toFixed(1)}%`;
        
        const formatNumber = (num, isShort) => isShort ? shortenNum(num) : formatFullNum(num);
        const useShort = window.appSettings.ui.shortNums;
        
        // Стандартные поля
        document.getElementById('t-dens-full').innerText = formatNumber(data.totals.t_dens, false);
        document.getElementById('t-dens-short').innerText = formatNumber(data.totals.t_dens, true);
        document.getElementById('r-dens-full').innerText = formatNumber(data.totals.r_dens, false);
        document.getElementById('r-dens-short').innerText = formatNumber(data.totals.r_dens, true);
        
        document.getElementById('t-prof-full').innerText = formatNumber(data.totals.t_prof, false);
        document.getElementById('t-prof-short').innerText = formatNumber(data.totals.t_prof, true);
        document.getElementById('r-prof-full').innerText = formatNumber(data.totals.r_prof, false);
        document.getElementById('r-prof-short').innerText = formatNumber(data.totals.r_prof, true);

        // Optimal Density & Verdict
        const optDens = data.totals.opt_dens;
        const optScu = data.totals.opt_scu;
        
        document.getElementById('opt-dens-full').innerText = formatNumber(optDens, false);
        document.getElementById('opt-dens-short').innerText = formatNumber(optDens, true);
        document.getElementById('opt-scu').innerText = optScu.toFixed(2);

        // Логика вердикта с использованием CSS-классов (никаких inline-стилей!)
        const verdictEl = document.getElementById('scan-verdict');
        let vText = "SKIP IT";
        let vClass = "verdict-skip"; 
        
        if (optDens >= 30000) { vText = "JACKPOT"; vClass = "verdict-jackpot"; } 
        else if (optDens >= 20000) { vText = "GOOD YIELD"; vClass = "verdict-good"; } 
        else if (optDens >= 12000) { vText = "AVERAGE"; vClass = "verdict-average"; }

        verdictEl.innerText = vText;
        verdictEl.className = `verdict-base ${vClass}`; // Применяем базовый класс + цвет
    },

    updateTable: function(mineralsData) {
        let html = "";
        
        mineralsData.forEach(chunk => {
            const minInfo = getMineralInfo(chunk.name);
            const gInfo = getGradeInfo(chunk.grade);
            
            // Заменяем inline-стили на логические классы
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
                        <span class="mineral-name" style="color: ${minInfo.color}; text-shadow: 0 0 5px ${minInfo.color};">
                            <span class="min-full">${minInfo.short === 'INER' ? 'INERT' : chunk.name.toUpperCase()}</span>
                            <span class="min-short hide">${minInfo.short}</span>
                        </span>
                        <span class="grade ${gInfo.text}">[${chunk.grade}]</span>
                    </div>
                </td>
                <td class="cell ui-col-comp">
                    <b>${chunk.percent.toFixed(2)}%</b>
                    <div class="bar-bg"><div class="bar-fill" style="background: ${minInfo.color}; width: ${Math.min(100, chunk.percent)}%; box-shadow: 0 0 5px ${minInfo.color};"></div></div>
                </td>
                <td class="cell ui-col-scu">
                    <div class="layout-container">
                        <span class="v-ref ui-ref-data">${chunk.scu_ref.toFixed(2)}</span>
                        <span class="v-raw ui-raw-data">${chunk.scu_raw.toFixed(2)}</span>
                    </div>
                </td>
                <td class="cell ui-col-dens">
                    <div class="layout-container">
                        <span class="v-ref ui-ref-data">
                            <span class="num-full hide">${formatFullNum(chunk.dens_ref)}</span><span class="num-short">${shortenNum(chunk.dens_ref)}</span>
                        </span>
                        <span class="v-raw ui-raw-data">
                            <span class="num-full hide">${formatFullNum(chunk.dens_raw)}</span><span class="num-short">${shortenNum(chunk.dens_raw)}</span>
                        </span>
                    </div>
                </td>
                <td class="cell ui-col-val text-right">
                    <div class="layout-container align-end">
                        <span class="v-ref ui-ref-data">
                            <span class="num-full hide">${formatFullNum(chunk.prof_ref)}</span><span class="num-short">${shortenNum(chunk.prof_ref)}</span>
                        </span>
                        <span class="v-raw ui-raw-data">
                            <span class="num-full hide">${formatFullNum(chunk.prof_raw)}</span><span class="num-short">${shortenNum(chunk.prof_raw)}</span>
                        </span>
                    </div>
                </td>
                <td class="cell ui-col-mods"><span class="mod-text">${modText}</span></td>
            </tr>`;
        });

        document.getElementById('minerals-body').innerHTML = html;
        this.applyFormatting(); 
    },

    // Читаем глобальные настройки appSettings, которые обновляет renderer.js
    applyFormatting: function() {
        const state = window.appSettings.ui;
        const toggleClass = (selector, shouldShow) => {
            document.querySelectorAll(selector).forEach(el => el.classList.toggle('hide', !shouldShow));
        };

        toggleClass('.ui-ref-data', state.showRef);
        toggleClass('.ui-raw-data', state.showRaw);
        document.querySelectorAll('.layout-container').forEach(el => el.classList.toggle('row-layout', state.isInline));
        toggleClass('.num-full', !state.shortNums);
        toggleClass('.num-short', state.shortNums);
        toggleClass('.min-full', !state.shortMins);
        toggleClass('.min-short', state.shortMins);

        Object.keys(state.cols).forEach(col => {
            toggleClass(`.ui-col-${col}`, state.cols[col]);
        });
    },

    flashScanFrame: function(top, left, width, height) {
        const frame = document.getElementById('visual-scan-frame');
        if (!frame) return;
        frame.style.top = top + 'px'; frame.style.left = left + 'px';
        frame.style.width = width + 'px'; frame.style.height = height + 'px';
        frame.style.transition = 'none'; frame.style.opacity = '1';
        setTimeout(() => { frame.style.transition = 'opacity 0.5s ease-out'; frame.style.opacity = '0'; }, 1500);
    }
};

// ============================================================================
// DRAG & DROP + 3D ПЕРСПЕКТИВА
// ============================================================================
let activePanel = null, offsetX, offsetY;

document.querySelectorAll('.drag-handle').forEach(handle => {
    handle.addEventListener('mousedown', (e) => {
        activePanel = handle.closest('.hologram-panel');
        activePanel.classList.add('dragging-active');
        const rect = activePanel.getBoundingClientRect();
        offsetX = e.clientX - rect.left; offsetY = e.clientY - rect.top;
    });
});

document.addEventListener('mousemove', (e) => {
    if (!activePanel) return;
    activePanel.style.left = (e.clientX - offsetX) + 'px';
    activePanel.style.top = (e.clientY - offsetY) + 'px';
    updateDistortion(activePanel);
});

document.addEventListener('mouseup', () => {
    if (activePanel) { activePanel.classList.remove('dragging-active'); activePanel = null; }
});

function updateDistortion(panel) {
    const rect = panel.getBoundingClientRect();
    const centerX = rect.left + (rect.width / 2), centerY = rect.top + (rect.height / 2);
    let normX = (centerX - window.innerWidth / 2) / (window.innerWidth / 2);
    let normY = (centerY - window.innerHeight / 2) / (window.innerHeight / 2);
    panel.style.transform = `perspective(1000px) rotateX(${normY * 3.0}deg) rotateY(${-normX * 25.0}deg) rotateZ(${normX * normY * 11.0}deg)`;
}

window.onload = () => document.querySelectorAll('.hologram-panel').forEach(p => updateDistortion(p));