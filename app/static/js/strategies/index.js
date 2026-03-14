// ======================================================================
// static/js/strategies/index.js
//
// Página /strategies — Vista de estrategias para todos los usuarios.
// Solo lectura: lista + ver detalles.
// ======================================================================

'use strict';

// ======================================================================
// Utilidades
// ======================================================================

function showAlert(msg, type = 'error') {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = `alert alert--${type}`;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 5000);
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function typeBadge(type) {
  const labels = { trend_following: 'Trend', mean_reversion: 'Mean Rev.' };
  const colors = { trend_following: 'var(--success,#4c8)', mean_reversion: 'var(--gold,#c8a050)' };
  const label = labels[type] || type;
  const color = colors[type] || 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${label}</span>`;
}

function regimeBadge(regime) {
  if (!regime) return '<span class="text-muted" style="font-size:0.8rem;">Cualquiera</span>';
  const colors = { trend_up: '#4c8', trend_down: '#e55', sideways: '#c8a050' };
  const labels = { trend_up: 'Alcista', trend_down: 'Bajista', sideways: 'Lateral' };
  const color = colors[regime] || 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${labels[regime] || regime}</span>`;
}

// ======================================================================
// API
// ======================================================================

async function fetchStrategies() {
  const res = await fetch('/api/strategies');
  return res.json();
}

// ======================================================================
// Render
// ======================================================================

function renderStrategies(strategies) {
  const tbody = document.getElementById('strategies-tbody');
  tbody.innerHTML = '';

  if (!strategies.length) {
    document.getElementById('table-wrapper').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    return;
  }

  document.getElementById('table-wrapper').classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');

  strategies.forEach(s => {
    const params = s.parameters || {};
    const rules = params.rules || [];
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.id}</td>
      <td style="font-weight:600;">${s.name}</td>
      <td><code style="font-size:0.75rem;">${s.version}</code></td>
      <td>${typeBadge(params.strategy_type)}</td>
      <td>${regimeBadge(params.regime_required)}</td>
      <td>${params.timeframe_code ? `<code style="font-size:0.75rem;">${params.timeframe_code}</code>` : '<span class="text-muted">—</span>'}</td>
      <td style="text-align:center;">${rules.length}</td>
      <td>${fmtDate(s.created_at)}</td>
      <td>
        <button class="btn btn--secondary" data-id="${s.id}" style="padding:0.3rem 0.6rem;font-size:0.75rem;">
          <i data-lucide="eye" style="width:12px;height:12px;"></i> Ver
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}

// ======================================================================
// Modal detalle
// ======================================================================

let allStrategies = [];

function openDetail(strategyId) {
  const s = allStrategies.find(x => x.id === strategyId);
  if (!s) return;
  const params = s.parameters || {};
  const rules = params.rules || [];

  document.getElementById('detail-title').textContent = `${s.name} v${s.version}`;
  document.getElementById('detail-type').textContent = params.strategy_type || '—';
  document.getElementById('detail-regime').innerHTML = regimeBadge(params.regime_required);
  document.getElementById('detail-tf').textContent = params.timeframe_code || '—';
  document.getElementById('detail-version').textContent = s.version;
  document.getElementById('detail-desc').textContent = s.description || 'Sin descripción.';
  document.getElementById('detail-params').textContent = JSON.stringify(params, null, 2);

  const rulesEl = document.getElementById('detail-rules');
  if (!rules.length) {
    rulesEl.innerHTML = '<span class="text-muted" style="font-size:0.85rem;">Sin reglas definidas.</span>';
  } else {
    rulesEl.innerHTML = rules.map(r => `
      <div style="display:flex;gap:0.5rem;align-items:center;padding:0.35rem 0.5rem;margin-bottom:0.25rem;
                  background:var(--surface-2,#1a1a2e);border-radius:5px;font-size:0.8rem;">
        <code style="color:var(--gold,#c8a050);">${r.indicator || '?'}</code>
        <span class="text-muted">${r.operator || '?'}</span>
        <strong>${r.value ?? '?'}</strong>
      </div>
    `).join('');
  }

  document.getElementById('modal-detail').classList.remove('hidden');
}

function closeDetail() {
  document.getElementById('modal-detail').classList.add('hidden');
}

// ======================================================================
// Init
// ======================================================================

async function loadStrategies() {
  try {
    const json = await fetchStrategies();
    allStrategies = Array.isArray(json.data) ? json.data : (json.data?.items || []);
    renderStrategies(allStrategies);
  } catch {
    showAlert('Error al cargar estrategias.');
  } finally {
    document.getElementById('table-loading').classList.add('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadStrategies();

  // Ver detalle (delegación de eventos)
  document.getElementById('strategies-tbody').addEventListener('click', e => {
    const btn = e.target.closest('button[data-id]');
    if (!btn) return;
    openDetail(parseInt(btn.dataset.id, 10));
  });

  // Cerrar modal
  document.getElementById('btn-detail-cancel').addEventListener('click', closeDetail);
  document.getElementById('modal-detail').addEventListener('click', e => {
    if (e.target.classList.contains('modal__backdrop')) closeDetail();
  });
});
