// ======================================================================
// static/js/accounts/index.js
//
// Gestión de cuentas de trading:
// - Listado, creación y edición de cuentas
// - Registro y consulta de balances
// ======================================================================

'use strict';

// ======================================================================
// Estado
// ======================================================================

let exchanges = [];
let currentAccountId = null;   // cuenta abierta en modal balances

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

function modeBadge(mode) {
  const color = mode === 'live' ? 'var(--danger, #e55)' : 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${mode.toUpperCase()}</span>`;
}

function statusBadge(status) {
  const color = status === 'active' ? 'var(--success, #4c8)' : 'var(--text-muted)';
  return `<span style="font-size:0.7rem;padding:2px 7px;border-radius:10px;background:${color}20;color:${color};font-weight:600;">${status}</span>`;
}

// ======================================================================
// API
// ======================================================================

async function fetchAccounts() {
  const res = await fetch('/accounts');
  return res.json();
}

async function fetchExchanges() {
  const res = await fetch('/exchanges');
  return res.json();
}

async function createAccount(body) {
  const res = await fetch('/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function updateAccount(id, body) {
  const res = await fetch(`/accounts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function fetchBalances(accountId, asset = '', limit = 100) {
  const params = new URLSearchParams({ limit });
  if (asset) params.set('asset', asset);
  const res = await fetch(`/accounts/${accountId}/balances?${params}`);
  return res.json();
}

async function recordBalance(accountId, body) {
  const res = await fetch(`/accounts/${accountId}/balances`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ======================================================================
// Render tabla de cuentas
// ======================================================================

function renderAccounts(accounts) {
  const tbody = document.getElementById('accounts-tbody');
  const loading = document.getElementById('table-loading');
  const wrapper = document.getElementById('table-wrapper');
  const empty = document.getElementById('empty-state');

  loading.classList.add('hidden');

  if (!accounts.length) {
    empty.classList.remove('hidden');
    return;
  }

  wrapper.classList.remove('hidden');

  tbody.innerHTML = accounts.map(a => {
    const exName = exchanges.find(e => e.id === a.exchange_id)?.name || (a.exchange_id ? `#${a.exchange_id}` : '—');
    const credIcon = a.has_credentials
      ? `<i data-lucide="lock" style="width:13px;color:var(--success,#4c8);" title="Cifradas"></i>`
      : `<span class="text-muted" style="font-size:0.75rem;">—</span>`;
    return `<tr>
      <td>${a.id}</td>
      <td>${a.name}</td>
      <td>${exName}</td>
      <td>${modeBadge(a.mode)}</td>
      <td>${a.base_currency}</td>
      <td>${statusBadge(a.status)}</td>
      <td style="text-align:center;">${credIcon}</td>
      <td>${fmtDate(a.created_at)}</td>
      <td>
        <div style="display:flex;gap:0.4rem;">
          <button class="btn btn--secondary btn-edit" data-id="${a.id}"
                  style="padding:0.3rem 0.6rem;font-size:0.75rem;width:auto;">
            <i data-lucide="pencil" style="width:12px;height:12px;"></i>
          </button>
          <button class="btn btn--secondary btn-balances" data-id="${a.id}" data-name="${a.name}"
                  style="padding:0.3rem 0.6rem;font-size:0.75rem;width:auto;">
            <i data-lucide="bar-chart-2" style="width:12px;height:12px;"></i>
          </button>
        </div>
      </td>
    </tr>`;
  }).join('');

  // Re-inicializar íconos lucide en contenido dinámico
  if (window.lucide) lucide.createIcons();
}

// ======================================================================
// Modal crear/editar cuenta
// ======================================================================

function populateExchangeSelect() {
  const sel = document.getElementById('sel-exchange');
  sel.innerHTML = '<option value="">Sin exchange</option>';
  exchanges.forEach(e => {
    const opt = document.createElement('option');
    opt.value = e.id;
    opt.textContent = `${e.name} (${e.type})`;
    sel.appendChild(opt);
  });
}

function openCreateModal() {
  document.getElementById('modal-title').textContent = 'Nueva cuenta';
  document.getElementById('btn-submit-text').textContent = 'Crear cuenta';
  document.getElementById('account-id').value = '';
  document.getElementById('form-account').reset();
  document.getElementById('group-status').classList.add('hidden');
  document.getElementById('form-error').classList.add('hidden');
  document.getElementById('modal-account').classList.remove('hidden');
}

function openEditModal(account) {
  document.getElementById('modal-title').textContent = 'Editar cuenta';
  document.getElementById('btn-submit-text').textContent = 'Guardar cambios';
  document.getElementById('account-id').value = account.id;
  document.getElementById('inp-name').value = account.name;
  document.getElementById('sel-mode').value = account.mode;
  document.getElementById('inp-currency').value = account.base_currency;
  document.getElementById('sel-exchange').value = account.exchange_id || '';
  document.getElementById('sel-status').value = account.status;
  document.getElementById('group-status').classList.remove('hidden');
  document.getElementById('inp-api-key').value = '';
  document.getElementById('inp-api-secret').value = '';
  document.getElementById('inp-creds-label').value = account.credentials_ref || '';
  document.getElementById('form-error').classList.add('hidden');
  document.getElementById('modal-account').classList.remove('hidden');
}

function closeAccountModal() {
  document.getElementById('modal-account').classList.add('hidden');
}

// ======================================================================
// Modal balances
// ======================================================================

function openBalancesModal(accountId, accountName) {
  currentAccountId = accountId;
  document.getElementById('balances-account-name').textContent = accountName;
  document.getElementById('inp-filter-asset').value = '';
  document.getElementById('balances-tbody').innerHTML = '';
  document.getElementById('balances-empty').classList.add('hidden');
  document.getElementById('balances-table-wrapper').classList.add('hidden');
  document.getElementById('modal-balances').classList.remove('hidden');
  loadBalances();
}

async function loadBalances() {
  const asset = document.getElementById('inp-filter-asset').value.trim();
  const loading = document.getElementById('balances-loading');
  const wrapper = document.getElementById('balances-table-wrapper');
  const empty = document.getElementById('balances-empty');

  loading.classList.remove('hidden');
  wrapper.classList.add('hidden');
  empty.classList.add('hidden');

  const data = await fetchBalances(currentAccountId, asset);
  loading.classList.add('hidden');

  const items = data.data?.items || [];
  if (!items.length) {
    empty.classList.remove('hidden');
    return;
  }

  wrapper.classList.remove('hidden');
  document.getElementById('balances-tbody').innerHTML = items.map(b => `
    <tr>
      <td><strong>${b.asset}</strong></td>
      <td>${parseFloat(b.free).toFixed(8)}</td>
      <td>${parseFloat(b.locked).toFixed(8)}</td>
      <td>${parseFloat(b.total).toFixed(8)}</td>
      <td style="font-size:0.75rem;color:var(--text-muted);">${b.ts ? new Date(b.ts).toLocaleString('es-ES') : '—'}</td>
    </tr>
  `).join('');
}

// ======================================================================
// Modal registrar balance
// ======================================================================

function openRecordBalanceModal() {
  document.getElementById('rb-account-id').value = currentAccountId;
  document.getElementById('rb-asset').value = document.getElementById('inp-filter-asset').value.trim();
  document.getElementById('rb-free').value = '0';
  document.getElementById('rb-locked').value = '0';
  document.getElementById('rb-error').classList.add('hidden');
  document.getElementById('modal-record-balance').classList.remove('hidden');
}

// ======================================================================
// Handlers de formularios
// ======================================================================

async function handleAccountSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('account-id').value;
  const isEdit = !!id;

  const spinner = document.getElementById('btn-submit-spinner');
  const btnText = document.getElementById('btn-submit-text');
  spinner.classList.remove('hidden');
  btnText.style.opacity = '0.5';

  const body = {
    name:              document.getElementById('inp-name').value.trim(),
    mode:              document.getElementById('sel-mode').value,
    base_currency:     document.getElementById('inp-currency').value.trim() || 'USD',
    exchange_id:       document.getElementById('sel-exchange').value ? parseInt(document.getElementById('sel-exchange').value) : null,
    api_key:           document.getElementById('inp-api-key').value || null,
    api_secret:        document.getElementById('inp-api-secret').value || null,
    credentials_label: document.getElementById('inp-creds-label').value.trim() || null,
  };

  if (isEdit) {
    body.status = document.getElementById('sel-status').value;
  }

  const data = isEdit ? await updateAccount(parseInt(id), body) : await createAccount(body);

  spinner.classList.add('hidden');
  btnText.style.opacity = '1';

  if (data.errorCode !== 0) {
    const errEl = document.getElementById('form-error');
    errEl.textContent = data.msg || 'Error inesperado.';
    errEl.classList.remove('hidden');
    return;
  }

  closeAccountModal();
  showAlert(isEdit ? 'Cuenta actualizada.' : 'Cuenta creada.', 'success');
  await loadPage();
}

async function handleRecordBalanceSubmit(e) {
  e.preventDefault();
  const accountId = parseInt(document.getElementById('rb-account-id').value);
  const body = {
    asset:  document.getElementById('rb-asset').value.trim(),
    free:   parseFloat(document.getElementById('rb-free').value) || 0,
    locked: parseFloat(document.getElementById('rb-locked').value) || 0,
  };

  const data = await recordBalance(accountId, body);
  if (data.errorCode !== 0) {
    const errEl = document.getElementById('rb-error');
    errEl.textContent = data.msg || 'Error al registrar.';
    errEl.classList.remove('hidden');
    return;
  }

  document.getElementById('modal-record-balance').classList.add('hidden');
  showAlert('Balance registrado.', 'success');
  await loadBalances();
}

// ======================================================================
// Carga inicial
// ======================================================================

async function loadPage() {
  document.getElementById('table-loading').classList.remove('hidden');
  document.getElementById('table-wrapper').classList.add('hidden');
  document.getElementById('empty-state').classList.add('hidden');

  const [accountsData, exchangesData] = await Promise.all([fetchAccounts(), fetchExchanges()]);
  exchanges = exchangesData.data?.items || [];
  populateExchangeSelect();

  const accounts = accountsData.data?.items || [];
  renderAccounts(accounts);
}

// ======================================================================
// Event listeners
// ======================================================================

document.addEventListener('DOMContentLoaded', async () => {
  await loadPage();

  // Abrir modal nueva cuenta
  document.getElementById('btn-new-account').addEventListener('click', openCreateModal);
  document.getElementById('btn-new-account-empty')?.addEventListener('click', openCreateModal);

  // Cerrar modales
  document.getElementById('btn-modal-close').addEventListener('click', closeAccountModal);
  document.getElementById('btn-cancel').addEventListener('click', closeAccountModal);
  document.getElementById('btn-balances-close').addEventListener('click', () => {
    document.getElementById('modal-balances').classList.add('hidden');
  });
  document.getElementById('btn-rb-close').addEventListener('click', () => {
    document.getElementById('modal-record-balance').classList.add('hidden');
  });
  document.getElementById('btn-rb-cancel').addEventListener('click', () => {
    document.getElementById('modal-record-balance').classList.add('hidden');
  });

  // Formulario cuenta
  document.getElementById('form-account').addEventListener('submit', handleAccountSubmit);

  // Balances
  document.getElementById('btn-load-balances').addEventListener('click', loadBalances);
  document.getElementById('btn-record-balance').addEventListener('click', openRecordBalanceModal);
  document.getElementById('form-record-balance').addEventListener('submit', handleRecordBalanceSubmit);

  // Delegación de eventos en tabla
  document.getElementById('accounts-tbody').addEventListener('click', async (e) => {
    const btnEdit = e.target.closest('.btn-edit');
    const btnBalances = e.target.closest('.btn-balances');

    if (btnEdit) {
      const id = parseInt(btnEdit.dataset.id);
      const res = await fetch(`/accounts/${id}`);
      const data = await res.json();
      if (data.errorCode === 0) openEditModal(data.data);
    }

    if (btnBalances) {
      openBalancesModal(parseInt(btnBalances.dataset.id), btnBalances.dataset.name);
    }
  });

  // Cerrar modales al click fuera
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.add('hidden');
    });
  });
});
