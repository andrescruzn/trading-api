// ======================================================================
// static/js/admin/strategies.js
//
// Página /admin/strategies — Gestión completa de estrategias (admin).
// CRUD: crear, editar, ver detalle.
// ======================================================================

'use strict';

// ======================================================================
// Estado
// ======================================================================

let allStrategies = [];
let editingId = null;  // null = crear, número = editar

// ======================================================================
// Utilidades
// ======================================================================

function showAlert(msg, type = 'error') {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = `alert alert--${type}`;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 6000);
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function typeBadge(type) {
  const labels = { trend_following: 'Trend', mean_reversion: 'Mean Rev.' };
  const colors = { trend_following: 'var(--success,#4c8)', mean_reversion: 'var(--gold,#c8a050)' };
  const color = colors[type] || 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${labels[type] || type}</span>`;
}

function regimeBadge(regime) {
  if (!regime) return '<span class="text-muted" style="font-size:0.8rem;">Cualquiera</span>';
  const colors = { trend_up: '#4c8', trend_down: '#e55', sideways: '#c8a050' };
  const labels = { trend_up: 'Alcista', trend_down: 'Bajista', sideways: 'Lateral' };
  const color = colors[regime] || 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${labels[regime] || regime}</span>`;
}

// ======================================================================
// Coherence hint (feedback en vivo al seleccionar tipo/régimen)
// ======================================================================

const ALLOWED_REGIMES = {
  trend_following: ['trend_up', 'trend_down'],
  mean_reversion:  ['sideways'],
};

function updateCoherenceHint() {
  const type   = document.getElementById('sel-type').value;
  const regime = document.getElementById('sel-regime').value;
  const hint   = document.getElementById('coherence-hint');

  if (!regime) {
    hint.classList.add('hidden');
    return;
  }

  const allowed = ALLOWED_REGIMES[type] || [];
  if (!allowed.includes(regime)) {
    hint.textContent = type === 'trend_following'
      ? '⚠️  Trend Following requiere régimen trend_up o trend_down, no sideways.'
      : '⚠️  Mean Reversion requiere régimen sideways, no tendencia.';
    hint.className = 'alert alert--error';
    hint.classList.remove('hidden');
  } else {
    hint.textContent = '✓  Coherencia correcta.';
    hint.className = 'alert alert--success';
    hint.classList.remove('hidden');
    setTimeout(() => hint.classList.add('hidden'), 3000);
  }
}

// ======================================================================
// API
// ======================================================================

async function fetchStrategies() {
  const res = await fetch('/api/strategies');
  return res.json();
}

async function createStrategy(body) {
  const res = await fetch('/api/strategies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function updateStrategy(id, body) {
  const res = await fetch(`/api/strategies/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ======================================================================
// Render tabla
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
    const rules  = params.rules || [];
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
      <td style="display:flex;gap:0.4rem;">
        <button class="btn btn--secondary btn-edit" data-id="${s.id}"
                style="padding:0.3rem 0.6rem;font-size:0.75rem;">
          <i data-lucide="pencil" style="width:12px;height:12px;"></i> Editar
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}

// ======================================================================
// Modal — abrir / cerrar
// ======================================================================

function openModal(strategy = null) {
  editingId = strategy ? strategy.id : null;
  const params = strategy?.parameters || {};

  document.getElementById('modal-title').textContent =
    strategy ? `Editar: ${strategy.name}` : 'Nueva estrategia';
  document.getElementById('btn-submit-text').textContent =
    strategy ? 'Guardar cambios' : 'Crear estrategia';
  document.getElementById('strategy-id').value = editingId || '';

  // Rellenar campos
  document.getElementById('inp-name').value        = strategy?.name || '';
  document.getElementById('inp-version').value     = strategy?.version || '1.0.0';
  document.getElementById('inp-description').value = strategy?.description || '';
  document.getElementById('sel-type').value        = params.strategy_type || 'trend_following';
  document.getElementById('sel-regime').value      = params.regime_required || '';
  document.getElementById('inp-tf').value          = params.timeframe_code || '';
  document.getElementById('inp-rules').value       =
    params.rules?.length ? JSON.stringify(params.rules, null, 2) : '';
  document.getElementById('inp-risk-pct').value    = params.risk_pct ?? 0.01;

  document.getElementById('form-error').classList.add('hidden');
  document.getElementById('coherence-hint').classList.add('hidden');
  document.getElementById('modal-strategy').classList.remove('hidden');
  document.getElementById('inp-name').focus();
}

function closeModal() {
  document.getElementById('modal-strategy').classList.add('hidden');
  editingId = null;
}

// ======================================================================
// Submit del formulario
// ======================================================================

async function handleSubmit(e) {
  e.preventDefault();

  const name        = document.getElementById('inp-name').value.trim();
  const version     = document.getElementById('inp-version').value.trim();
  const description = document.getElementById('inp-description').value.trim() || null;
  const type        = document.getElementById('sel-type').value;
  const regime      = document.getElementById('sel-regime').value || null;
  const tf          = document.getElementById('inp-tf').value.trim() || null;
  const riskPct     = parseFloat(document.getElementById('inp-risk-pct').value) || 0.01;

  // Parsear rules
  let rules = [];
  const rulesRaw = document.getElementById('inp-rules').value.trim();
  if (rulesRaw) {
    try {
      rules = JSON.parse(rulesRaw);
      if (!Array.isArray(rules)) throw new Error('rules debe ser un array');
    } catch (err) {
      document.getElementById('form-error').textContent =
        `Reglas inválidas: ${err.message}`;
      document.getElementById('form-error').classList.remove('hidden');
      return;
    }
  }

  const parameters = {
    strategy_type:   type,
    regime_required: regime,
    timeframe_code:  tf,
    rules,
    risk_pct:        riskPct,
  };

  // Deshabilitar botón
  const btn = document.getElementById('btn-submit');
  const spinner = document.getElementById('btn-submit-spinner');
  btn.disabled = true;
  spinner.classList.remove('hidden');
  document.getElementById('form-error').classList.add('hidden');

  try {
    const body = { name, version, description, parameters };
    const json = editingId
      ? await updateStrategy(editingId, body)
      : await createStrategy(body);

    if (json.errorCode >= 400) {
      document.getElementById('form-error').textContent = json.msg || 'Error desconocido.';
      document.getElementById('form-error').classList.remove('hidden');
      return;
    }

    showAlert(
      editingId ? 'Estrategia actualizada.' : 'Estrategia creada.',
      'success',
    );
    closeModal();
    await loadStrategies();
  } catch {
    document.getElementById('form-error').textContent = 'Error de conexión.';
    document.getElementById('form-error').classList.remove('hidden');
  } finally {
    btn.disabled = false;
    spinner.classList.add('hidden');
  }
}

// ======================================================================
// Carga inicial
// ======================================================================

async function loadStrategies() {
  document.getElementById('table-loading').classList.remove('hidden');
  document.getElementById('table-wrapper').classList.add('hidden');
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

// ======================================================================
// Init
// ======================================================================

document.addEventListener('DOMContentLoaded', () => {
  loadStrategies();

  // Abrir modal nuevo
  document.getElementById('btn-new-strategy').addEventListener('click', () => openModal());
  document.getElementById('btn-new-strategy-empty')?.addEventListener('click', () => openModal());

  // Editar (delegación)
  document.getElementById('strategies-tbody').addEventListener('click', e => {
    const btn = e.target.closest('.btn-edit');
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);
    const strategy = allStrategies.find(s => s.id === id);
    if (strategy) openModal(strategy);
  });

  // Cerrar modal
  document.getElementById('btn-cancel').addEventListener('click', closeModal);
  document.getElementById('modal-strategy').addEventListener('click', e => {
    if (e.target.classList.contains('modal__backdrop')) closeModal();
  });

  // Submit
  document.getElementById('form-strategy').addEventListener('submit', handleSubmit);

  // Coherencia en vivo
  document.getElementById('sel-type').addEventListener('change', updateCoherenceHint);
  document.getElementById('sel-regime').addEventListener('change', updateCoherenceHint);
});
