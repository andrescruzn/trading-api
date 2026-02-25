// market/candles.js

document.addEventListener('DOMContentLoaded', function () {
  loadSymbols();
  loadTimeframes();
  document.getElementById('btn-load').addEventListener('click', loadCandles);

  // Pre-seleccionar desde query string si viene de /market/symbols
  const params = new URLSearchParams(window.location.search);
  const preSymbol = params.get('symbol_id');
  if (preSymbol) {
    // Esperar a que los selects estén cargados
    setTimeout(function () {
      const sel = document.getElementById('sel-symbol');
      if (sel) sel.value = preSymbol;
    }, 600);
  }
});

async function loadSymbols() {
  try {
    const res = await fetch('/symbols?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-symbol');
    (json.data || []).forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.symbol;
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

async function loadCandles() {
  clearAlert();
  const symbolId = document.getElementById('sel-symbol').value;
  const timeframeId = document.getElementById('sel-timeframe').value;
  const limit = document.getElementById('sel-limit').value;

  if (!symbolId || !timeframeId) {
    showAlert('Selecciona un símbolo y un timeframe.', 'error');
    return;
  }

  showTableLoading(true);
  try {
    const qs = new URLSearchParams({ symbol_id: symbolId, timeframe_id: timeframeId, limit });
    const res = await fetch('/candles?' + qs, { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) { showAlert(json.msg || 'Error al cargar velas.', 'error'); return; }
    renderTable(json.data || []);
  } catch {
    showAlert('Error de conexión.', 'error');
  } finally {
    showTableLoading(false);
  }
}

function renderTable(items) {
  const tbody = document.getElementById('candles-tbody');
  tbody.innerHTML = '';
  const summary = document.getElementById('candles-summary');

  if (!items.length) {
    summary.textContent = '';
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin velas para este criterio.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }

  summary.textContent = items.length + ' velas (más reciente primero)';
  items.forEach(function (c) {
    const tr = document.createElement('tr');
    const ts = c.ts ? c.ts.substring(0, 19).replace('T', ' ') : '—';
    tr.innerHTML =
      '<td>' + ts + '</td>' +
      '<td>' + fmt(c.open) + '</td>' +
      '<td>' + fmt(c.high) + '</td>' +
      '<td>' + fmt(c.low) + '</td>' +
      '<td>' + fmt(c.close) + '</td>' +
      '<td>' + fmt(c.volume) + '</td>';
    tbody.appendChild(tr);
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

function fmt(val) {
  if (val === null || val === undefined) return '—';
  const n = parseFloat(val);
  return isNaN(n) ? val : n.toLocaleString('en-US', { maximumFractionDigits: 8 });
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
