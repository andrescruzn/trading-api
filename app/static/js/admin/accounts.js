// ======================================================================
// static/js/admin/accounts.js
//
// Vista admin: todas las cuentas del sistema (solo lectura).
// ======================================================================

'use strict';

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

async function loadAccounts() {
  const loading = document.getElementById('table-loading');
  const wrapper = document.getElementById('table-wrapper');
  const empty = document.getElementById('empty-state');
  const alertEl = document.getElementById('alert-msg');

  try {
    const res = await fetch('/accounts');
    const data = await res.json();

    loading.classList.add('hidden');

    if (data.errorCode !== 0) {
      alertEl.textContent = data.msg || 'Error al cargar cuentas.';
      alertEl.className = 'alert alert--error';
      alertEl.classList.remove('hidden');
      return;
    }

    const accounts = data.data?.items || [];
    if (!accounts.length) {
      empty.classList.remove('hidden');
      return;
    }

    wrapper.classList.remove('hidden');
    document.getElementById('accounts-tbody').innerHTML = accounts.map(a => {
      const credIcon = a.has_credentials
        ? `<i data-lucide="lock" style="width:13px;color:var(--success,#4c8);" title="Cifradas"></i>`
        : `<span class="text-muted" style="font-size:0.75rem;">—</span>`;
      return `<tr>
        <td>${a.id}</td>
        <td>${a.user_id}</td>
        <td>${a.name}</td>
        <td>${a.exchange_id ?? '—'}</td>
        <td>${modeBadge(a.mode)}</td>
        <td>${a.base_currency}</td>
        <td>${statusBadge(a.status)}</td>
        <td style="text-align:center;">${credIcon}</td>
        <td>${fmtDate(a.created_at)}</td>
        <td>
          <a href="/accounts" style="font-size:0.75rem;color:var(--gold);">Ver detalle</a>
        </td>
      </tr>`;
    }).join('');

    if (window.lucide) lucide.createIcons();
  } catch {
    loading.classList.add('hidden');
    alertEl.textContent = 'Error de conexión.';
    alertEl.className = 'alert alert--error';
    alertEl.classList.remove('hidden');
  }
}

document.addEventListener('DOMContentLoaded', loadAccounts);
