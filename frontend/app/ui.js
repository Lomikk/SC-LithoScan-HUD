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

function shortenNum(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(2) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "k";
    return Math.floor(num).toString();
}

function getGradeInfo(grade) {
    if (grade < 300) return { text: "grade-trash", row: "" };
    if (grade < 500) return { text: "grade-base", row: "" };
    if (grade < 700) return { text: "grade-uncommon", row: "" };
    if (grade < 850) return { text: "grade-rare", row: "" };
    if (grade < 950) return { text: "grade-epic", row: "row-glow-epic" };
    return { text: "grade-legendary", row: "row-glow-legendary" };
}

// Текущее состояние интерфейса (чтобы сохранять настройки чекбоксов после обновления таблицы)
const uiState = {
    showRef: true, showRaw: true, isInline: false,
    shortNums: true, shortMins: false,
    cols: { comp: true, scu: true, dens: true, val: true, mods: true }
};

// ============================================================================
// ГЕНЕРАЦИЯ HTML
// ============================================================================
const UI = {
    updateTotals: function(data) {
        document.getElementById('meta-vol').innerText = `VOL: ${data.meta_vol.toFixed(1)} SCU`;
        document.getElementById('meta-method').innerText = `METHOD: ${data.meta_method}`;
        document.getElementById('meta-bonus').innerText = `BONUS: +${data.meta_bonus.toFixed(1)}%`;
        
        const formatNumber = (num, isShort) => isShort ? shortenNum(num) : Math.round(num).toLocaleString('en-US');
        
        // Стандартные поля
        document.getElementById('t-dens-full').innerText = formatNumber(data.totals.t_dens, false);
        document.getElementById('t-dens-short').innerText = formatNumber(data.totals.t_dens, true);
        document.getElementById('r-dens-full').innerText = formatNumber(data.totals.r_dens, false);
        document.getElementById('r-dens-short').innerText = formatNumber(data.totals.r_dens, true);
        
        document.getElementById('t-prof-full').innerText = formatNumber(data.totals.t_prof, false);
        document.getElementById('t-prof-short').innerText = formatNumber(data.totals.t_prof, true);
        document.getElementById('r-prof-full').innerText = formatNumber(data.totals.r_prof, false);
        document.getElementById('r-prof-short').innerText = formatNumber(data.totals.r_prof, true);

        // ====================================================================
        // НОВОЕ: ВЫВОД OPTIMAL DENSITY И ВЕРДИКТА
        // ====================================================================
        const optDens = data.totals.opt_dens;
        const optScu = data.totals.opt_scu;
        
        document.getElementById('opt-dens').innerText = formatNumber(optDens, false);
        document.getElementById('opt-scu').innerText = optScu.toFixed(1);

        // Логика вердикта (подсказка игроку)
    const verdictEl = document.getElementById('scan-verdict');
    let vText = "SKIP IT";
    let vColor = "#ff4d4d"; 
    
    if (optDens >= 30000) {
        vText = "JACKPOT";
        vColor = "#ffb800"; 
    } else if (optDens >= 20000) {
        vText = "GOOD YIELD";
        vColor = "#00ff9d"; 
    } else if (optDens >= 12000) {
        vText = "AVERAGE";
        vColor = "#3498db"; 
    }

    verdictEl.innerText = vText;
    verdictEl.style.color = vColor;
    // Добавим легкое текстовое свечение, чтобы не было скучно
    verdictEl.style.textShadow = `0 0 10px ${vColor}aa`;
    },

    updateTable: function(mineralsData) {
        let html = "";
        
        mineralsData.forEach(chunk => {
            const minInfo = getMineralInfo(chunk.name);
            const gInfo = getGradeInfo(chunk.grade);
            const opacityStyle = minInfo.short === "INER" ? "opacity: 0.5;" : "";
            
            let modText = "-";
            if (chunk.bonus > 0) {
                let sysColor = "#a0aec0"; // Дефолтный серый
                
                if (chunk.system === "Stanton") sysColor = "#29B6F6"; // Синий
                else if (chunk.system === "Pyro") sysColor = "#F44336"; // Красный
                else if (chunk.system === "Nyx") sysColor = "#FF6D00"; // Оранжевый

                // Окрашиваем только название станции
                modText = `<span style="color: ${sysColor}; text-shadow: 0 0 5px ${sysColor};">${chunk.station}</span> (+${(chunk.bonus * 100).toFixed(0)}%)`;
            }

            // Шаблонная строка (Backticks) - идеальная замена f-строкам Python
            // === НОВОЕ: ОПРЕДЕЛЯЕМ КЛАСС ДЛЯ ШТРИХОВКИ ===
            const coreClass = chunk.is_core ? "row-core" : "row-trash";

            // Добавляем coreClass в список классов тега <tr>
            html += `
            <tr class="${gInfo.row} ${coreClass}" style="${opacityStyle}">
                <td class="cell ui-col-mineral">
                    <div class="layout-container align-items-baseline">
                        <span class="mineral-name" style="color: ${minInfo.color};">
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
                            <span class="num-full hide">${Math.round(chunk.dens_ref).toLocaleString('en-US')}</span><span class="num-short">${shortenNum(chunk.dens_ref)}</span>
                        </span>
                        <span class="v-raw ui-raw-data">
                            <span class="num-full hide">${Math.round(chunk.dens_raw).toLocaleString('en-US')}</span><span class="num-short">${shortenNum(chunk.dens_raw)}</span>
                        </span>
                    </div>
                </td>
                <td class="cell ui-col-val" style="text-align: right;">
                    <div class="layout-container" style="align-items: flex-end;">
                        <span class="v-ref ui-ref-data">
                            <span class="num-full hide">${Math.round(chunk.prof_ref).toLocaleString('en-US')}</span><span class="num-short">${shortenNum(chunk.prof_ref)}</span>
                        </span>
                        <span class="v-raw ui-raw-data">
                            <span class="num-full hide">${Math.round(chunk.prof_raw).toLocaleString('en-US')}</span><span class="num-short">${shortenNum(chunk.prof_raw)}</span>
                        </span>
                    </div>
                </td>
                <td class="cell ui-col-mods"><span class="mod-text">${modText}</span></td>
            </tr>`;
        });

        document.getElementById('minerals-body').innerHTML = html;
        this.applyFormatting(); // Восстанавливаем состояние чекбоксов для новых строк
    },

    // ========================================================================
    // ЛОГИКА ИНТЕРФЕЙСА И ЧЕКБОКСОВ
    // ========================================================================
    applyFormatting: function() {
        const toggleClass = (selector, shouldShow) => {
            document.querySelectorAll(selector).forEach(el => el.classList.toggle('hide', !shouldShow));
        };

        toggleClass('.ui-ref-data', uiState.showRef);
        toggleClass('.ui-raw-data', uiState.showRaw);
        
        document.querySelectorAll('.layout-container').forEach(el => el.classList.toggle('row-layout', uiState.isInline));
        
        toggleClass('.num-full', !uiState.shortNums);
        toggleClass('.num-short', uiState.shortNums);
        toggleClass('.min-full', !uiState.shortMins);
        toggleClass('.min-short', uiState.shortMins);

        Object.keys(uiState.cols).forEach(col => {
            toggleClass(`.ui-col-${col}`, uiState.cols[col]);
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