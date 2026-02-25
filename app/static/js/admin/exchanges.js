// admin/exchanges.js
// CSP: sin onclick inline — todos los handlers via addEventListener

let editingId = null;
let allItems = [];
let currentPage = 1;
const PAGE_SIZE = 20;

// ======================================================================
// Inicialización
// ======================================================================
document.addEventListener('DOMContentLoaded', function () {
  loadExchanges();
  document.getElementById('btn-new-exchange').addEventListener('click', openNewModal);
  document.getElementById('btn-save-exchange').addEventListener('click', saveExchange);
  document.getElementById('btn-cancel-exchange').addEventListener('click', closeModal);
  document.querySelector('.modal__backdrop').addEventListener('click', closeModal);
  document.getElementById('pag-prev').addEventListener('click', function () { renderPage(currentPage - 1); });
  document.getElementById('pag-next').addEventListener('click', function () { renderPage(currentPage + 1); });
});

// ======================================================================
// Cargar lista
// ======================================================================
async function loadExchanges() {
  showTableLoading(true);
  try {
    const res = await fetch('/exchanges', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) { showAlert(json.msg || 'Error al cargar exchanges', 'error'); return; }
    allItems = json.data || [];
    renderPage(1);
  } catch {
    showAlert('Error de conexión', 'error');
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
  const tbody = document.getElementById('exchanges-tbody');
  tbody.innerHTML = '';
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin exchanges registrados.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }
  items.forEach(function (ex) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + ex.id + '</td>' +
      '<td>' + ex.name + '</td>' +
      '<td>' + ex.type + '</td>' +
      '<td>' + (ex.is_active ? '<span class="badge badge--success">Activo</span>' : '<span class="badge badge--muted">Inactivo</span>') + '</td>' +
      '<td>' + (ex.created_at ? ex.created_at.substring(0, 10) : '—') + '</td>' +
      '<td><button class="btn btn--secondary btn--sm" data-id="' + ex.id + '" data-name="' + ex.name + '" data-type="' + ex.type + '" data-active="' + ex.is_active + '">Editar</button></td>';
    tbody.appendChild(tr);
  });
  tbody.querySelectorAll('button[data-id]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      openEditModal(
        parseInt(btn.dataset.id),
        btn.dataset.name,
        btn.dataset.type,
        btn.dataset.active === 'true'
      );
    });
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

// ======================================================================
// Modal
// ======================================================================
function openNewModal() {
  editingId = null;
  document.getElementById('modal-title').textContent = 'Nuevo exchange';
  document.getElementById('inp-name').value = '';
  document.getElementById('inp-type').value = 'crypto_exchange';
  document.getElementById('group-is-active').style.display = 'none';
  clearModalAlert();
  document.getElementById('modal-exchange').classList.remove('hidden');
}

function openEditModal(id, name, type, isActive) {
  editingId = id;
  document.getElementById('modal-title').textContent = 'Editar exchange';
  document.getElementById('inp-name').value = name;
  document.getElementById('inp-type').value = type;
  document.getElementById('inp-is-active').checked = isActive;
  document.getElementById('group-is-active').style.display = 'block';
  clearModalAlert();
  document.getElementById('modal-exchange').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-exchange').classList.add('hidden');
}

// ======================================================================
// Guardar (crear o actualizar)
// ======================================================================
async function saveExchange() {
  const name = document.getElementById('inp-name').value.trim();
  const type = document.getElementById('inp-type').value;
  const isActive = document.getElementById('inp-is-active').checked;

  if (!name) { showModalAlert('El nombre es requerido.', 'error'); return; }

  const btn = document.getElementById('btn-save-exchange');
  btn.disabled = true;

  try {
    let res, json;
    if (editingId === null) {
      res = await fetch('/exchanges', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type }),
      });
    } else {
      res = await fetch('/exchanges/' + editingId, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, is_active: isActive }),
      });
    }
    json = await res.json();
    if (!res.ok) { showModalAlert(json.msg || 'Error al guardar.', 'error'); return; }
    closeModal();
    showAlert(editingId === null ? 'Exchange creado.' : 'Exchange actualizado.', 'success');
    loadExchanges();
  } catch {
    showModalAlert('Error de conexión.', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ======================================================================
// Helpers UI
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
