const API_BASE = '';
const chartDefaults = {
    responsive: true, maintainAspectRatio: true,
    plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } } },
    scales: {
        x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } }
    }
};

let charts = {}, fireMap = null, mapMarkers = [];
let lastPrediction = null, predictionHistory = [];

async function api(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) {
        let detail = `${res.status}`;
        try {
            const err = await res.json();
            if (err.detail) detail = Array.isArray(err.detail) ? err.detail.map(d => d.msg || d).join(', ') : String(err.detail);
        } catch {}
        throw new Error(`API ${endpoint}: ${detail}`);
    }
    return res.json();
}

function animateCounter(el, target, duration = 1200, suffix = '') {
    const startTime = performance.now();
    const isFloat = !Number.isInteger(target);
    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        el.textContent = isFloat ? current.toFixed(1) + suffix : Math.floor(current).toLocaleString('fr-FR') + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function formatDate(iso) {
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function riskColor(level) {
    if (level === 'Élevé') return '#ef4444';
    if (level === 'Modéré') return '#f59e0b';
    return '#22c55e';
}

function riskBadge(level) {
    const cls = level === 'Élevé' ? 'high' : level === 'Modéré' ? 'medium' : 'low';
    return `<span class="badge ${cls}">${level}</span>`;
}

function graviteDots(n) {
    return '<span class="gravite-dots">' + Array.from({length:5}, (_, i) => `<span class="gravite-dot ${i < n ? 'active' : ''}"></span>`).join('') + '</span>';
}

function initScrollAnimations() {
    const observer = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }), { threshold: 0.1 });
    document.querySelectorAll('[data-animate]').forEach(el => { if (!el.classList.contains('kpi-card')) observer.observe(el); });
}

function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            document.querySelector(item.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth' });
        });
    });
    document.getElementById('menuToggle')?.addEventListener('click', () => document.getElementById('sidebar').classList.toggle('open'));
}

async function checkHealth() {
    const dot = document.getElementById('statusDot'), text = document.getElementById('statusText');
    try {
        const health = await api('/api/health');
        dot.className = 'status-dot online';
        text.textContent = health.mongodb ? 'MongoDB connecté · API active' : 'Mode CSV · MongoDB hors ligne';
        return health;
    } catch {
        dot.className = 'status-dot offline';
        text.textContent = 'API hors ligne';
        return null;
    }
}

async function loadKPIs() {
    const stats = await api('/api/stats');
    animateCounter(document.getElementById('kpiTotal'), stats.total_incidents);
    const highRisk = stats.par_risque?.['Élevé'] || 0;
    animateCounter(document.getElementById('kpiHighRisk'), highRisk);
    document.getElementById('kpiHighPct').textContent = stats.total_incidents ? ((highRisk / stats.total_incidents) * 100).toFixed(1) + '% du total' : '—';
    animateCounter(document.getElementById('kpiDamage'), stats.degats_totaux_eur);
    try {
        const metrics = await api('/api/ml/metrics');
        document.getElementById('kpiAccuracy').textContent = (metrics.accuracy * 100).toFixed(1) + '%';
    } catch { document.getElementById('kpiAccuracy').textContent = 'N/A'; }
    document.getElementById('lastUpdate').textContent = 'Màj ' + new Date().toLocaleTimeString('fr-FR');
    return stats;
}

function destroyChart(id) { if (charts[id]) { charts[id].destroy(); delete charts[id]; } }

async function loadMonthlyChart() {
    const data = await api('/api/trends/monthly');
    destroyChart('monthly');
    const ctx = document.getElementById('chartMonthly').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(255,107,53,0.3)'); gradient.addColorStop(1, 'rgba(255,107,53,0)');
    charts.monthly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.periode),
            datasets: [
                { label: 'Incidents', data: data.map(d => d.incidents), borderColor: '#ff6b35', backgroundColor: gradient, fill: true, tension: 0.4, pointRadius: 3 },
                { label: 'Gravité moy.', data: data.map(d => d.gravite_moyenne), borderColor: '#a855f7', borderDash: [5,5], tension: 0.4, yAxisID: 'y1' }
            ]
        },
        options: { ...chartDefaults, scales: { x: chartDefaults.scales.x, y: { ...chartDefaults.scales.y, position: 'left' }, y1: { position: 'right', ticks: { color: '#64748b' }, grid: { display: false }, min: 0, max: 5 } } }
    });
}

function loadTypesChart(stats) {
    destroyChart('types');
    const types = stats.par_type || {};
    charts.types = new Chart(document.getElementById('chartTypes'), {
        type: 'doughnut',
        data: { labels: Object.keys(types), datasets: [{ data: Object.values(types), backgroundColor: ['#ff6b35','#ef4444','#fbbf24','#22c55e','#3b82f6','#a855f7'], borderWidth: 0, hoverOffset: 8 }] },
        options: { responsive: true, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 12, font: { size: 11 } } } } }
    });
}

function loadRiskChart(stats) {
    destroyChart('risk');
    const risks = stats.par_risque || {}, order = ['Faible','Modéré','Élevé'];
    charts.risk = new Chart(document.getElementById('chartRisk'), {
        type: 'bar',
        data: { labels: order.filter(k => risks[k] !== undefined), datasets: [{ data: order.map(k => risks[k] || 0), backgroundColor: ['#22c55e','#f59e0b','#ef4444'], borderRadius: 8, barThickness: 40 }] },
        options: { ...chartDefaults, plugins: { legend: { display: false } } }
    });
}

async function loadHourlyChart() {
    const data = await api('/api/hourly-distribution');
    destroyChart('hourly');
    const ctx = document.getElementById('chartHourly').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(239,68,68,0.5)'); gradient.addColorStop(1, 'rgba(239,68,68,0.05)');
    charts.hourly = new Chart(ctx, { type: 'bar', data: { labels: data.map(d => d.heure + 'h'), datasets: [{ data: data.map(d => d.count), backgroundColor: gradient, borderRadius: 6 }] }, options: { ...chartDefaults, plugins: { legend: { display: false } } } });
}

async function loadQuartiersChart() {
    const data = await api('/api/quartiers');
    destroyChart('quartiers');
    charts.quartiers = new Chart(document.getElementById('chartQuartiers'), {
        type: 'bar',
        data: { labels: data.map(d => d.quartier), datasets: [{ data: data.map(d => d.count), backgroundColor: data.map((_, i) => `hsla(${20 + i * 15}, 90%, 55%, 0.7)`), borderRadius: 6 }] },
        options: { indexAxis: 'y', ...chartDefaults, plugins: { legend: { display: false } } }
    });
}

async function loadFeaturesChart() {
    try {
        const data = await api('/api/ml/feature-importance');
        destroyChart('features');
        const top = data.slice(0, 10);
        charts.features = new Chart(document.getElementById('chartFeatures'), {
            type: 'bar',
            data: { labels: top.map(f => f.feature), datasets: [{ data: top.map(f => f.importance), backgroundColor: 'rgba(255,107,53,0.7)', borderRadius: 6 }] },
            options: { indexAxis: 'y', ...chartDefaults, plugins: { legend: { display: false } } }
        });
    } catch {}
}

async function initMap() {
    if (fireMap) return;
    fireMap = L.map('fireMap').setView([45.764, 4.835], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; OSM &copy; CARTO', subdomains: 'abcd', maxZoom: 19 }).addTo(fireMap);
    const data = await api('/api/heatmap');
    mapMarkers.forEach(m => fireMap.removeLayer(m)); mapMarkers = [];
    data.forEach((point, i) => {
        const color = riskColor(point.niveau_risque);
        const marker = L.circleMarker([point.latitude, point.longitude], { radius: 4 + point.gravite, fillColor: color, color, weight: 1, opacity: 0.8, fillOpacity: 0.5 }).addTo(fireMap);
        marker.bindPopup(`<strong>${point.quartier}</strong><br>Risque: ${point.niveau_risque}<br>Gravité: ${point.gravite}/5`);
        setTimeout(() => marker.setStyle({ fillOpacity: 0.7 }), i * 5);
        mapMarkers.push(marker);
    });
}

async function loadPredictionHistory() {
    const { predictions } = await api('/api/ml/history?limit=50');
    predictionHistory = predictions;
    const tbody = document.getElementById('historyBody');
    if (!predictions.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-row">Aucune analyse pour le moment</td></tr>';
        return;
    }
    tbody.innerHTML = predictions.map((p, i) => `
        <tr style="animation-delay:${i * 0.05}s" class="${i === 0 ? 'row-latest' : ''}">
            <td><code style="font-size:0.75rem;color:#ff6b35">${p.id || '—'}</code></td>
            <td>${formatDate(p.timestamp)}</td><td>${p.quartier}</td><td>${p.type_incendie}</td>
            <td>${riskBadge(p.niveau_risque_predit)}</td><td>${(p.confiance * 100).toFixed(1)}%</td>
            <td><div class="export-cell">
                <button class="btn-export btn-export-sm" data-id="${p.id}" data-fmt="pdf">PDF</button>
                <button class="btn-export btn-export-sm" data-id="${p.id}" data-fmt="csv">CSV</button>
                <button class="btn-export btn-export-sm" data-id="${p.id}" data-fmt="json">JSON</button>
            </div></td>
        </tr>`).join('');
    tbody.querySelectorAll('[data-id]').forEach(btn => {
        btn.addEventListener('click', () => exportPrediction(btn.dataset.id, btn.dataset.fmt));
    });
}

function findPrediction(id) {
    return predictionHistory.find(p => p.id === id) || (lastPrediction?.id === id ? lastPrediction : null);
}

function downloadFile(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
}

function predictionToRows(p) {
    return [
        ['ID', p.id || '—'], ['Date', formatDate(p.timestamp)], ['Quartier', p.quartier],
        ['Type incendie', p.type_incendie], ['Origine', p.origine], ['Mois', p.mois],
        ['Heure', p.heure + 'h'], ['Température', p.temperature_c + ' °C'],
        ['Humidité', p.humidite_pct + ' %'], ['Vent', p.vent_vitesse_kmh + ' km/h'],
        ['Indice sécheresse', p.indice_secheresse], ['Risque prédit', p.niveau_risque_predit],
        ['Confiance', (p.confiance * 100).toFixed(1) + ' %'],
        ['Prob. Faible', ((p.probabilites?.Faible || 0) * 100).toFixed(1) + ' %'],
        ['Prob. Modéré', ((p.probabilites?.Modéré || 0) * 100).toFixed(1) + ' %'],
        ['Prob. Élevé', ((p.probabilites?.Élevé || 0) * 100).toFixed(1) + ' %'],
    ];
}

async function downloadPdf(url, filename) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Export PDF échoué');
    const blob = await res.blob();
    downloadFile(blob, filename, 'application/pdf');
}

async function exportPrediction(id, format) {
    const p = findPrediction(id);
    if (!p) return alert('Analyse introuvable');
    try {
        if (format === 'pdf') await downloadPdf(`/api/ml/export/${encodeURIComponent(id)}/pdf`, `fireguard_${id}.pdf`);
        else if (format === 'csv') {
            const rows = predictionToRows(p);
            downloadFile('\ufeff' + 'Paramètre,Valeur\n' + rows.map(r => `"${r[0]}","${r[1]}"`).join('\n'), `fireguard_${id}.csv`, 'text/csv');
        } else downloadFile(JSON.stringify(p, null, 2), `fireguard_${id}.json`, 'application/json');
    } catch (e) { alert('Erreur export: ' + e.message); }
}

async function exportAllPredictions(format) {
    if (!predictionHistory.length) return alert('Aucune analyse à exporter');
    try {
        if (format === 'pdf') await downloadPdf('/api/ml/export/all/pdf', 'fireguard_historique.pdf');
        else {
            const header = 'ID,Date,Quartier,Type,Origine,Risque,Confiance,Température,Humidité,Vent';
            const rows = predictionHistory.map(p => [p.id, p.timestamp, p.quartier, p.type_incendie, p.origine, p.niveau_risque_predit, p.confiance, p.temperature_c, p.humidite_pct, p.vent_vitesse_kmh].map(v => `"${v}"`).join(','));
            downloadFile('\ufeff' + header + '\n' + rows.join('\n'), 'fireguard_historique.csv', 'text/csv');
        }
    } catch (e) { alert('Erreur export: ' + e.message); }
}

function initExportButtons() {
    document.getElementById('exportActions')?.addEventListener('click', e => {
        const btn = e.target.closest('[data-format]');
        if (btn && lastPrediction) exportPrediction(lastPrediction.id, btn.dataset.format);
    });
    document.getElementById('exportAllPdf')?.addEventListener('click', () => exportAllPredictions('pdf'));
    document.getElementById('exportAllCsv')?.addEventListener('click', () => exportAllPredictions('csv'));
}

async function loadIncidents() {
    const risk = document.getElementById('filterRisk').value, type = document.getElementById('filterType').value;
    let url = '/api/incidents?limit=30';
    if (risk) url += `&niveau_risque=${encodeURIComponent(risk)}`;
    if (type) url += `&type_incendie=${encodeURIComponent(type)}`;
    const { incidents } = await api(url);
    document.getElementById('incidentsBody').innerHTML = incidents.map((inc, i) => `
        <tr style="animation-delay:${i * 0.05}s">
            <td><code style="font-size:0.75rem;color:#ff6b35">${inc.id}</code></td>
            <td>${formatDate(inc.date_heure)}</td><td>${inc.quartier}</td><td>${inc.type_incendie}</td>
            <td>${graviteDots(inc.gravite)}</td><td>${riskBadge(inc.niveau_risque)}</td><td>${inc.surface_m2} m²</td>
        </tr>`).join('');
}

function initPrediction() {
    document.getElementById('predictForm').addEventListener('submit', async e => {
        e.preventDefault();
        const btn = e.target.querySelector('.btn-predict');
        btn.classList.add('loading');
        const formData = new FormData(e.target);
        const numericFields = new Set(['mois','heure','temperature_c','humidite_pct','vent_vitesse_kmh','indice_secheresse']);
        const intFields = new Set(['mois','heure']);
        const payload = {};
        formData.forEach((val, key) => {
            payload[key] = numericFields.has(key) ? (intFields.has(key) ? parseInt(val, 10) : parseFloat(val)) : val;
        });
        payload.jour_semaine = new Date().getDay();
        try {
            const result = await api('/api/ml/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            lastPrediction = { ...payload, ...result };
            showPrediction(lastPrediction);
            await loadPredictionHistory();
            document.getElementById('history')?.scrollIntoView({ behavior: 'smooth' });
        } catch (err) { alert('Erreur de prédiction: ' + err.message); }
        finally { btn.classList.remove('loading'); }
    });
}

function showPrediction(result) {
    document.querySelector('.result-placeholder').classList.add('hidden');
    document.getElementById('resultContent').classList.remove('hidden');
    const level = result.niveau_risque_predit, color = riskColor(level);
    const offsets = { 'Faible': 170, 'Modéré': 100, 'Élevé': 30 };
    const fill = document.getElementById('gaugeFill');
    fill.style.stroke = color; fill.style.strokeDashoffset = offsets[level] || 100;
    const label = document.getElementById('gaugeLabel');
    label.textContent = level; label.style.color = color;
    const bars = document.getElementById('probBars');
    bars.innerHTML = Object.entries(result.probabilites).map(([cls, prob]) => `
        <div class="prob-bar"><span class="prob-bar-label">${cls}</span>
        <div class="prob-bar-track"><div class="prob-bar-fill" style="background:${riskColor(cls)};width:0" data-width="${(prob * 100).toFixed(1)}%"></div></div>
        <span style="font-size:0.8rem;color:#94a3b8;width:40px">${(prob * 100).toFixed(1)}%</span></div>`).join('');
    requestAnimationFrame(() => bars.querySelectorAll('.prob-bar-fill').forEach(el => { el.style.width = el.dataset.width; }));
    document.getElementById('confidence').textContent = `Confiance du modèle : ${(result.confiance * 100).toFixed(1)}%`;
}

async function loadDashboard() {
    await checkHealth();
    const stats = await loadKPIs();
    loadTypesChart(stats); loadRiskChart(stats);
    await Promise.all([loadMonthlyChart(), loadHourlyChart(), loadQuartiersChart(), loadFeaturesChart(), loadIncidents(), loadPredictionHistory()]);
    await initMap();
}

document.addEventListener('DOMContentLoaded', () => {
    initNavigation(); initScrollAnimations(); initPrediction(); initExportButtons();
    document.getElementById('btnRefresh').addEventListener('click', loadDashboard);
    document.getElementById('filterRisk').addEventListener('change', loadIncidents);
    document.getElementById('filterType').addEventListener('change', loadIncidents);
    loadDashboard();
    setInterval(checkHealth, 30000);
});
