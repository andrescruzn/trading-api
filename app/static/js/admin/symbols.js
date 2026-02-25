// admin/symbols.js

let editingId = null;
let exchangesCache = [];
let allItems = [];
let currentPage = 1;
const PAGE_SIZE = 20;

document.addEventListener('DOMContentLoaded', function () {
  loadExchanges().then(loadSymbols);
  document.getElementById('btn-new-symbol').addEventListener('click', openNewModal);
  document.getElementById('btn-filter').addEventListener('click', applyFilters);
  document.getElementById('btn-save-symbol').addEventListener('click', saveSymbol);
  document.getElementById('btn-cancel-symbol').addEventListener('click', closeModal);
  document.querySelector('.modal__backdrop').addEventListener('click', closeModal);
  document.getElementById('pag-prev').addEventListener('click', function () { renderPage(currentPage - 1); });
  document.getElementById('pag-next').addEventListener('click', function () { renderPage(currentPage + 1); });
});

// ======================================================================
// Cargar exchanges para selects
// ======================================================================
async function loadExchanges() {
  try {
    const res = await fetch('/exchanges?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    exchangesCache = json.data || [];
    populateExchangeSelects();
  } catch {}
}

function populateExchangeSelects() {
  ['filter-exchange', 'inp-exchange'].forEach(function (id) {
    const sel = document.getElementById(id);
    if (!sel) return;
    const hasAll = id === 'filter-exchange';
    sel.innerHTML = hasAll ? '<option value="">Todos</option>' : '';
    exchangesCache.forEach(function (ex) {
      const opt = document.createElement('option');
      opt.value = ex.id;
      opt.textContent = ex.name;
      sel.appendChild(opt);
    });
  });
}

// ======================================================================
// Cargar lista
// ======================================================================
async function loadSymbols(params) {
  showTableLoading(true);
  const qs = params ? '?' + new URLSearchParams(params).toString() : '?is_active=true';
  try {
    const res = await fetch('/symbols' + qs, { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) { showAlert(json.msg || 'Error al cargar.', 'error'); return; }
    allItems = json.data || [];
    renderPage(1);
  } catch {
    showAlert('Error de conexión.', 'error');
  } finally {
    showTableLoading(false);
  }
}

function getExchangeName(id) {
  const ex = exchangesCache.find(function (e) { return e.id === id; });
  return ex ? ex.name : id;
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
  const tbody = document.getElementById('symbols-tbody');
  tbody.innerHTML = '';
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Sin símbolos.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }
  items.forEach(function (s) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + s.id + '</td>' +
      '<td>' + getExchangeName(s.exchange_id) + '</td>' +
      '<td><strong>' + s.symbol + '</strong></td>' +
      '<td>' + (s.base_asset || '—') + '</td>' +
      '<td>' + (s.quote_asset || '—') + '</td>' +
      '<td>' + s.asset_class + '</td>' +
      '<td>' + (s.is_active ? '<span class="badge badge--success">Activo</span>' : '<span class="badge badge--muted">Inactivo</span>') + '</td>' +
      '<td><button class="btn btn--secondary btn--sm" data-id="' + s.id + '">Editar</button></td>';
    tbody.appendChild(tr);
    tr.querySelector('button[data-id]').addEventListener('click', function () { loadAndEdit(s); });
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

// ======================================================================
// Filtros
// ======================================================================
function applyFilters() {
  const params = {};
  const ex = document.getElementById('filter-exchange').value;
  const ac = document.getElementById('filter-asset-class').value;
  const act = document.getElementById('filter-active').value;
  if (ex) params.exchange_id = ex;
  if (ac) params.asset_class = ac;
  if (act) params.is_active = act;
  loadSymbols(Object.keys(params).length ? params : null);
}

// ======================================================================
// Modal
// ======================================================================
function openNewModal() {
  editingId = null;
  document.getElementById('modal-title').textContent = 'Nuevo símbolo';
  document.getElementById('inp-exchange').value = '';
  document.getElementById('inp-symbol').value = '';
  document.getElementById('inp-asset-class').value = 'crypto';
  document.getElementById('inp-base').value = '';
  document.getElementById('inp-quote').value = '';
  document.getElementById('inp-is-active').checked = true;
  document.getElementById('group-exchange').style.display = 'block';
  document.getElementById('inp-symbol').disabled = false;
  document.getElementById('group-is-active').style.display = 'none';
  clearModalAlert();
  document.getElementById('modal-symbol').classList.remove('hidden');
}

function loadAndEdit(s) {
  editingId = s.id;
  document.getElementById('modal-title').textContent = 'Editar símbolo';
  document.getElementById('group-exchange').style.display = 'none';
  document.getElementById('inp-symbol').value = s.symbol;
  document.getElementById('inp-symbol').disabled = true;
  document.getElementById('inp-asset-class').value = s.asset_class;
  document.getElementById('inp-base').value = s.base_asset || '';
  document.getElementById('inp-quote').value = s.quote_asset || '';
  document.getElementById('inp-is-active').checked = s.is_active;
  document.getElementById('group-is-active').style.display = 'block';
  clearModalAlert();
  document.getElementById('modal-symbol').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-symbol').classList.add('hidden');
}

// ======================================================================
// Guardar
// ======================================================================
async function saveSymbol() {
  const btn = document.getElementById('btn-save-symbol');
  btn.disabled = true;
  try {
    let res, json;
    if (editingId === null) {
      const exchangeId = document.getElementById('inp-exchange').value;
      const symbol = document.getElementById('inp-symbol').value.trim();
      if (!exchangeId) { showModalAlert('Selecciona un exchange.', 'error'); return; }
      if (!symbol) { showModalAlert('El símbolo es requerido.', 'error'); return; }
      res = await fetch('/symbols', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exchange_id: parseInt(exchangeId),
          symbol,
          asset_class: document.getElementById('inp-asset-class').value,
          base_asset: document.getElementById('inp-base').value.trim() || null,
          quote_asset: document.getElementById('inp-quote').value.trim() || null,
        }),
      });
    } else {
      res = await fetch('/symbols/' + editingId, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_class: document.getElementById('inp-asset-class').value,
          base_asset: document.getElementById('inp-base').value.trim() || null,
          quote_asset: document.getElementById('inp-quote').value.trim() || null,
          is_active: document.getElementById('inp-is-active').checked,
        }),
      });
    }
    json = await res.json();
    if (!res.ok) { showModalAlert(json.msg || 'Error al guardar.', 'error'); return; }
    closeModal();
    showAlert(editingId === null ? 'Símbolo creado.' : 'Símbolo actualizado.', 'success');
    loadSymbols();
  } catch {
    showModalAlert('Error de conexión.', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ======================================================================
// UI helpers
// ======================================================================
function showTableLoading(show) {
  document.getElementById('table-loading').classList.toggle('hidden', !show);
  if (show) document.getElementById('table-wrapper').classList.add('hidden');
}

function showAlert(msg, type) {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
  setTimeout(function () { el.className = 'alert hidden'; }, 4000);
}

function showModalAlert(msg, type) {
  const el = document.getElementById('modal-alert');
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
}

function clearModalAlert() {
  const el = document.getElementById('modal-alert');
  el.className = 'alert hidden';
  el.textContent = '';
}
