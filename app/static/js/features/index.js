// features/index.js
// CSP: sin onclick inline — todos los handlers via addEventListener

document.addEventListener('DOMContentLoaded', function () {
  loadSymbols();
  loadTimeframes();
  loadFeatureSets();
  document.getElementById('btn-load').addEventListener('click', loadFeatures);
});

// ======================================================================
// Cargar selects
// ======================================================================
async function loadSymbols() {
  try {
    const res = await fetch('/symbols?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-symbol');
    (json.data || []).forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.exchange_name ? s.symbol + ' (' + s.exchange_name + ')' : s.symbol;
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadTimeframes() {
  try {
    const res = await fetch('/timeframes', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-timeframe');
    (json.data || []).forEach(function (tf) {
      const opt = document.createElement('option');
      opt.value = tf.id;
      opt.textContent = tf.code;
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadFeatureSets() {
  try {
    const res = await fetch('/feature-sets', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-feature-set');
    (json.data || []).forEach(function (fs) {
      const opt = document.createElement('option');
      opt.value = fs.id;
      opt.textContent = fs.name + ' v' + fs.version;
      sel.appendChild(opt);
    });
  } catch {}
}

// ======================================================================
// Cargar indicadores
// ======================================================================
async function loadFeatures() {
  clearAlert();
  const symbolId = document.getElementById('sel-symbol').value;
  const timeframeId = document.getElementById('sel-timeframe').value;
  const featureSetId = document.getElementById('sel-feature-set').value;
  const limit = document.getElementById('sel-limit').value;

  if (!symbolId || !timeframeId || !featureSetId) {
    showAlert('Selecciona símbolo, timeframe y feature set.', 'error');
    return;
  }

  showTableLoading(true);
  try {
    const qs = new URLSearchParams({ symbol_id: symbolId, timeframe_id: timeframeId, feature_set_id: featureSetId, limit });
    const res = await fetch('/candle-features?' + qs, { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) { showAlert(json.msg || 'Error al cargar indicadores.', 'error'); return; }
    renderTable(json.data || []);
  } catch {
    showAlert('Error de conexión.', 'error');
  } finally {
    showTableLoading(false);
  }
}

// ======================================================================
// Renderizar tabla
// ======================================================================
function renderTable(items) {
  const tbody = document.getElementById('features-tbody');
  tbody.innerHTML = '';
  const summary = document.getElementById('features-summary');

  if (!items.length) {
    summary.textContent = '';
    tbody.innerHTML = '<tr><td colspan="12" class="text-center text-muted">Sin indicadores para este criterio. Calcula primero desde Admin → Feature Sets.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }

  summary.textContent = items.length + ' filas (más reciente primero)';
  items.forEach(function (row) {
    const f = row.features || {};
    const tr = document.createElement('tr');
    const ts = row.ts ? row.ts.substring(0, 19).replace('T', ' ') : '—';
    const regime = f.regime || '—';
    const regimeClass = regime === 'trend_up' ? 'badge--success' : regime === 'trend_down' ? 'badge--error' : 'badge--muted';
    tr.innerHTML =
      '<td>' + ts + '</td>' +
      '<td><span class="badge ' + regimeClass + '">' + regime + '</span></td>' +
      '<td>' + fmt(f.rsi_14) + '</td>' +
      '<td>' + fmt(f.ema_20) + '</td>' +
      '<td>' + fmt(f.ema_50) + '</td>' +
      '<td>' + fmt(f.ema_200) + '</td>' +
      '<td>' + fmt(f.macd) + '</td>' +
      '<td>' + fmt(f.macd_signal) + '</td>' +
      '<td>' + fmt(f.atr_14) + '</td>' +
      '<td>' + fmt(f.bb_upper) + '</td>' +
      '<td>' + fmt(f.bb_lower) + '</td>' +
      '<td>' + fmt(f.vol_rel) + '</td>';
    tbody.appendChild(tr);
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

// ======================================================================
// Helpers
// ======================================================================
function fmt(val) {
  if (val === null || val === undefined) return '—';
  const n = parseFloat(val);
  return isNaN(n) ? val : n.toLocaleString('en-US', { maximumFractionDigits: 6 });
}

function showTableLoading(show) {
  document.getElementById('table-loading').classList.toggle('hidden', !show);
  if (show) document.getElementById('table-wrapper').classList.add('hidden');
}

function showAlert(msg, type) {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
}

function clearAlert() {
  const el = document.getElementById('alert-msg');
  el.className = 'alert hidden';
  el.textContent = '';
}
