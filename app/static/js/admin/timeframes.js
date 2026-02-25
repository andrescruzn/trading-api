// admin/timeframes.js

let allItems = [];
let currentPage = 1;
const PAGE_SIZE = 20;

document.addEventListener('DOMContentLoaded', function () {
  loadTimeframes();
  document.getElementById('btn-new-tf').addEventListener('click', openModal);
  document.getElementById('btn-save-tf').addEventListener('click', saveTf);
  document.getElementById('btn-cancel-tf').addEventListener('click', closeModal);
  document.querySelector('.modal__backdrop').addEventListener('click', closeModal);
  document.getElementById('pag-prev').addEventListener('click', function () { renderPage(currentPage - 1); });
  document.getElementById('pag-next').addEventListener('click', function () { renderPage(currentPage + 1); });
});

async function loadTimeframes() {
  showTableLoading(true);
  try {
    const res = await fetch('/timeframes', { credentials: 'include' });
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

function humanDuration(seconds) {
  if (seconds < 60) return seconds + 's';
  if (seconds < 3600) return (seconds / 60) + 'm';
  if (seconds < 86400) return (seconds / 3600) + 'h';
  return (seconds / 86400) + 'd';
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
  const tbody = document.getElementById('tf-tbody');
  tbody.innerHTML = '';
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Sin timeframes registrados.</td></tr>';
    document.getElementById('table-wrapper').classList.remove('hidden');
    return;
  }
  items.forEach(function (tf) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + tf.id + '</td>' +
      '<td><strong>' + tf.code + '</strong></td>' +
      '<td>' + tf.seconds + '</td>' +
      '<td>' + humanDuration(tf.seconds) + '</td>';
    tbody.appendChild(tr);
  });
  document.getElementById('table-wrapper').classList.remove('hidden');
}

function openModal() {
  document.getElementById('inp-code').value = '';
  document.getElementById('inp-seconds').value = '';
  clearModalAlert();
  document.getElementById('modal-tf').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-tf').classList.add('hidden');
}

async function saveTf() {
  const code = document.getElementById('inp-code').value.trim();
  const seconds = parseInt(document.getElementById('inp-seconds').value);
  if (!code) { showModalAlert('El código es requerido.', 'error'); return; }
  if (!seconds || seconds < 1) { showModalAlert('Los segundos deben ser mayor a 0.', 'error'); return; }

  const btn = document.getElementById('btn-save-tf');
  btn.disabled = true;
  try {
    const res = await fetch('/timeframes', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, seconds }),
    });
    const json = await res.json();
    if (!res.ok) { showModalAlert(json.msg || 'Error al guardar.', 'error'); return; }
    closeModal();
    showAlert('Timeframe creado.', 'success');
    loadTimeframes();
  } catch {
    showModalAlert('Error de conexión.', 'error');
  } finally {
    btn.disabled = false;
  }
}

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
