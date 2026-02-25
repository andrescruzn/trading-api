// market/symbols.js

let exchangesCache = [];
let allItems = [];
let currentPage = 1;
const PAGE_SIZE = 20;

document.addEventListener('DOMContentLoaded', function () {
  loadExchanges().then(function () { loadSymbols(); });
  document.getElementById('btn-filter').addEventListener('click', applyFilters);
  document.getElementById('pag-prev').addEventListener('click', function () { renderPage(currentPage - 1); });
  document.getElementById('pag-next').addEventListener('click', function () { renderPage(currentPage + 1); });
});

async function loadExchanges() {
  try {
    const res = await fetch('/exchanges?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    exchangesCache = json.data || [];
    const sel = document.getElementById('filter-exchange');
    exchangesCache.forEach(function (ex) {
      const opt = document.createElement('option');
      opt.value = ex.id;
      opt.textContent = ex.name;
      sel.appendChild(opt);
    });
  } catch {}
}

function getExchangeName(id) {
  const ex = exchangesCache.find(function (e) { return e.id === id; });
  return ex ? ex.name : id;
}

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
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin símbolos disponibles.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }
  items.forEach(function (s) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td><strong>' + s.symbol + '</strong></td>' +
      '<td>' + getExchangeName(s.exchange_id) + '</td>' +
      '<td>' + (s.base_asset || '—') + '</td>' +
      '<td>' + (s.quote_asset || '—') + '</td>' +
      '<td>' + s.asset_class + '</td>' +
      '<td><a href="/market/candles?symbol_id=' + s.id + '" class="btn btn--secondary btn--sm">Ver velas</a></td>';
    tbody.appendChild(tr);
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

function applyFilters() {
  const params = {};
  const ex = document.getElementById('filter-exchange').value;
  const ac = document.getElementById('filter-asset-class').value;
  if (ex) params.exchange_id = ex;
  if (ac) params.asset_class = ac;
  params.is_active = 'true';
  loadSymbols(params);
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
