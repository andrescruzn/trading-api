"use strict";

// ======================================================================
// admin/managed_accounts.js
// Gestión de cuentas gestionadas
// ======================================================================

const API = "/api/managed-accounts";

async function loadAccounts() {
  const loading = document.getElementById("ma-loading");
  const table   = document.getElementById("ma-table");
  const empty   = document.getElementById("ma-empty");
  const tbody   = document.getElementById("ma-body");

  loading.style.display = "block";
  table.style.display   = "none";
  empty.style.display   = "none";

  try {
    const res  = await fetch(API, { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : [];

    loading.style.display = "none";

    if (items.length === 0) { empty.style.display = "block"; return; }

    const periodLabel = { daily: "Diario", weekly: "Semanal", monthly: "Mensual" };

    tbody.innerHTML = items.map(a => `
      <tr>
        <td>${a.id}</td>
        <td style="font-weight:500;">${a.name}</td>
        <td>${a.investor_id}</td>
        <td>${a.account_id}</td>
        <td>${a.bot_id || '—'}</td>
        <td>$${parseFloat(a.initial_capital).toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
        <td style="color:var(--gold);">$${parseFloat(a.high_water_mark).toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
        <td><span class="period-badge period--${a.period_type}">${periodLabel[a.period_type] || a.period_type}</span></td>
        <td><span class="status--${a.is_active ? 'active' : 'inactive'}" style="padding:0.2rem 0.6rem;border-radius:20px;font-size:0.7rem;font-weight:600;">${a.is_active ? 'Activo' : 'Inactivo'}</span></td>
        <td>
          <button class="btn btn--ghost" style="font-size:0.75rem;padding:0.2rem 0.6rem;" onclick="openEditModal(${JSON.stringify(a).replace(/"/g,'&quot;')})">
            Editar
          </button>
        </td>
      </tr>
    `).join("");

    table.style.display = "table";
  } catch (e) {
    loading.textContent = "Error al cargar.";
  }
}

// ── Crear ────────────────────────────────────────────────────────────

function openCreateModal() {
  ["inp-name","inp-investor-id","inp-account-id","inp-capital","inp-bot-id"].forEach(id => {
    document.getElementById(id).value = "";
  });
  document.getElementById("inp-period-type").value = "monthly";
  document.getElementById("create-error").style.display = "none";
  document.getElementById("modal-create").style.display = "flex";
}

function closeCreateModal() {
  document.getElementById("modal-create").style.display = "none";
}

async function submitCreate() {
  const name       = document.getElementById("inp-name").value.trim();
  const investorId = parseInt(document.getElementById("inp-investor-id").value);
  const accountId  = parseInt(document.getElementById("inp-account-id").value);
  const capital    = parseFloat(document.getElementById("inp-capital").value);
  const periodType = document.getElementById("inp-period-type").value;
  const botIdRaw   = document.getElementById("inp-bot-id").value;
  const botId      = botIdRaw ? parseInt(botIdRaw) : null;

  if (!name || !investorId || !accountId || isNaN(capital)) {
    showError("create-error", "Completa los campos obligatorios.");
    return;
  }

  const body = { name, investor_id: investorId, account_id: accountId, initial_capital: capital, period_type: periodType };
  if (botId) body.bot_id = botId;

  try {
    const res  = await fetch(API, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) { showError("create-error", json.msg || "Error al crear."); return; }
    closeCreateModal();
    loadAccounts();
  } catch (e) {
    showError("create-error", "Error de red.");
  }
}

// ── Editar ───────────────────────────────────────────────────────────

function openEditModal(a) {
  document.getElementById("edit-id").value          = a.id;
  document.getElementById("edit-name").value        = a.name;
  document.getElementById("edit-bot-id").value      = a.bot_id || "";
  document.getElementById("edit-period-type").value = a.period_type;
  document.getElementById("edit-is-active").checked = a.is_active;
  document.getElementById("edit-error").style.display = "none";
  document.getElementById("modal-edit").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("modal-edit").style.display = "none";
}

async function submitEdit() {
  const id         = document.getElementById("edit-id").value;
  const name       = document.getElementById("edit-name").value.trim();
  const botIdRaw   = document.getElementById("edit-bot-id").value;
  const periodType = document.getElementById("edit-period-type").value;
  const isActive   = document.getElementById("edit-is-active").checked;

  const body = { name: name || undefined, period_type: periodType, is_active: isActive };
  if (botIdRaw) body.bot_id = parseInt(botIdRaw);

  try {
    const res  = await fetch(`${API}/${id}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) { showError("edit-error", json.msg || "Error al actualizar."); return; }
    closeEditModal();
    loadAccounts();
  } catch (e) {
    showError("edit-error", "Error de red.");
  }
}

function showError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent   = msg;
  el.style.display = "block";
}

document.querySelectorAll(".modal-overlay").forEach(o => {
  o.addEventListener("click", e => { if (e.target === o) o.style.display = "none"; });
});

loadAccounts();
