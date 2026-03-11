// admin/feature_sets.js
// CSP: sin onclick inline — todos los handlers via addEventListener

let allItems = [];
let currentPage = 1;
const PAGE_SIZE = 20;

// ======================================================================
// Inicialización
// ======================================================================
document.addEventListener('DOMContentLoaded', function () {
  loadFeatureSets();

  // Modal nuevo feature set
  document.getElementById('btn-new-fs').addEventListener('click', openNewFsModal);
  document.getElementById('btn-save-fs').addEventListener('click', saveFeatureSet);
  document.getElementById('btn-cancel-fs').addEventListener('click', closeFsModal);
  document.querySelector('#modal-fs .modal__backdrop').addEventListener('click', closeFsModal);

  // Modal calcular
  document.getElementById('btn-calculate').addEventListener('click', openCalcModal);
  document.getElementById('btn-run-calc').addEventListener('click', runCalculate);
  document.getElementById('btn-cancel-calc').addEventListener('click', closeCalcModal);
  document.querySelector('#modal-calculate .modal__backdrop').addEventListener('click', closeCalcModal);

  // Paginación
  document.getElementById('pag-prev').addEventListener('click', function () { renderPage(currentPage - 1); });
  document.getElementById('pag-next').addEventListener('click', function () { renderPage(currentPage + 1); });
});

// ======================================================================
// Cargar feature sets
// ======================================================================
async function loadFeatureSets() {
  showTableLoading(true);
  try {
    const res = await fetch('/feature-sets', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) { showAlert(json.msg || 'Error al cargar feature sets.', 'error'); return; }
    allItems = json.data || [];
    renderPage(1);
  } catch {
    showAlert('Error de conexión.', 'error');
  } finally {
    showTableLoading(false);
  }
}

function renderPage(page) {
  currentPage = page;
  const total = allItems.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  currentPage = Math.min(Math.max(1, currentPage), totalPages);
  const slice = allItems.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  renderTable(slice);
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) { pag.classList.add('hidden'); return; }
  pag.classList.remove('hidden');
  document.getElementById('pag-info').textContent = 'Página ' + currentPage + ' de ' + totalPages + ' (' + total + ' registros)';
  document.getElementById('pag-prev').disabled = currentPage <= 1;
  document.getElementById('pag-next').disabled = currentPage >= totalPages;
}

function renderTable(items) {
  const tbody = document.getElementById('fs-tbody');
  tbody.innerHTML = '';
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin feature sets registrados.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }
  items.forEach(function (fs) {
    const tr = document.createElement('tr');
    const specStr = fs.spec ? JSON.stringify(fs.spec).substring(0, 60) + '…' : '—';
    const createdAt = fs.created_at ? fs.created_at.substring(0, 10) : '—';
    tr.innerHTML =
      '<td>' + fs.id + '</td>' +
      '<td>' + escHtml(fs.name) + '</td>' +
      '<td>' + escHtml(fs.version) + '</td>' +
      '<td>' + escHtml(fs.description || '—') + '</td>' +
      '<td><code style="font-size:0.75rem;">' + escHtml(specStr) + '</code></td>' +
      '<td>' + createdAt + '</td>';
    tbody.appendChild(tr);
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

// ======================================================================
// Modal — nuevo feature set
// ======================================================================
function openNewFsModal() {
  document.getElementById('inp-name').value = '';
  document.getElementById('inp-version').value = '1.0.0';
  document.getElementById('inp-description').value = '';
  document.getElementById('inp-spec').value = '';
  clearModalAlert('modal-alert');
  document.getElementById('modal-fs').classList.remove('hidden');
}

function closeFsModal() {
  document.getElementById('modal-fs').classList.add('hidden');
}

async function saveFeatureSet() {
  const name = document.getElementById('inp-name').value.trim();
  const version = document.getElementById('inp-version').value.trim();
  const description = document.getElementById('inp-description').value.trim();
  const specRaw = document.getElementById('inp-spec').value.trim();

  if (!name) { showModalAlert('modal-alert', 'El nombre es requerido.', 'error'); return; }
  if (!specRaw) { showModalAlert('modal-alert', 'El spec es requerido.', 'error'); return; }

  let spec;
  try {
    spec = JSON.parse(specRaw);
  } catch {
    showModalAlert('modal-alert', 'El spec no es JSON válido.', 'error');
    return;
  }

  const btn = document.getElementById('btn-save-fs');
  btn.disabled = true;
  try {
    const res = await fetch('/feature-sets', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, version, description: description || null, spec }),
    });
    const json = await res.json();
    if (!res.ok) { showModalAlert('modal-alert', json.msg || 'Error al guardar.', 'error'); return; }
    closeFsModal();
    showAlert('Feature set creado.', 'success');
    loadFeatureSets();
  } catch {
    showModalAlert('modal-alert', 'Error de conexión.', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ======================================================================
// Modal — calcular indicadores
// ======================================================================
async function openCalcModal() {
  clearModalAlert('calc-alert');
  await Promise.all([loadCalcSymbols(), loadCalcTimeframes(), loadCalcFeatureSets()]);
  document.getElementById('modal-calculate').classList.remove('hidden');
}

function closeCalcModal() {
  document.getElementById('modal-calculate').classList.add('hidden');
}

async function loadCalcSymbols() {
  try {
    const res = await fetch('/symbols?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('calc-symbol');
    sel.innerHTML = '<option value="">Selecciona...</option>';
    (json.data || []).forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.exchange_name ? s.symbol + ' (' + s.exchange_name + ')' : s.symbol;
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadCalcTimeframes() {
  try {
    const res = await fetch('/timeframes', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('calc-timeframe');
    sel.innerHTML = '<option value="">Selecciona...</option>';
    (json.data || []).forEach(function (tf) {
      const opt = document.createElement('option');
      opt.value = tf.id;
      opt.textContent = tf.code;
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadCalcFeatureSets() {
  try {
    const res = await fetch('/feature-sets', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('calc-fs');
    sel.innerHTML = '<option value="">Selecciona...</option>';
    (json.data || []).forEach(function (fs) {
      const opt = document.createElement('option');
      opt.value = fs.id;
      opt.textContent = fs.name + ' v' + fs.version;
      sel.appendChild(opt);
    });
  } catch {}
}

async function runCalculate() {
  const symbolId = document.getElementById('calc-symbol').value;
  const timeframeId = document.getElementById('calc-timeframe').value;
  const featureSetId = document.getElementById('calc-fs').value;

  if (!symbolId || !timeframeId || !featureSetId) {
    showModalAlert('calc-alert', 'Selecciona símbolo, timeframe y feature set.', 'error');
    return;
  }

  const btn = document.getElementById('btn-run-calc');
  btn.disabled = true;
  btn.textContent = 'Calculando...';
  clearModalAlert('calc-alert');

  try {
    const res = await fetch('/candle-features/calculate', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol_id: parseInt(symbolId),
        timeframe_id: parseInt(timeframeId),
        feature_set_id: parseInt(featureSetId),
      }),
    });
    const json = await res.json();
    if (!res.ok) {
      showModalAlert('calc-alert', json.msg || 'Error al calcular.', 'error');
      return;
    }
    const d = json.data || {};
    const msg = 'Calculado: ' + (d.rows_calculated || 0) + ' filas, ' + (d.rows_affected || 0) + ' guardadas.';
    closeCalcModal();
    showAlert(msg, 'success');
  } catch {
    showModalAlert('calc-alert', 'Error de conexión.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="cpu"></i> Calcular';
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
}

// ======================================================================
// Helpers
// ======================================================================
function showTableLoading(show) {
  document.getElementById('table-loading').classList.toggle('hidden', !show);
  if (show) document.getElementById('table-wrapper').classList.add('hidden');
}

function showAlert(msg, type) {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
  setTimeout(function () { el.className = 'alert hidden'; }, 5000);
}

function showModalAlert(elId, msg, type) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
}

function clearModalAlert(elId) {
  const el = document.getElementById(elId);
  el.className = 'alert hidden';
  el.textContent = '';
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
