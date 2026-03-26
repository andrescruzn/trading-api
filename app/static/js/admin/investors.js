"use strict";

// ======================================================================
// admin/investors.js
// Gestión de inversores — CRUD
// ======================================================================

const API = "/api/investors";

async function loadInvestors() {
  const loading = document.getElementById("investors-loading");
  const table   = document.getElementById("investors-table");
  const empty   = document.getElementById("investors-empty");
  const tbody   = document.getElementById("investors-body");

  loading.style.display = "block";
  table.style.display   = "none";
  empty.style.display   = "none";

  try {
    const res  = await fetch(API, { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : [];

    loading.style.display = "none";

    if (items.length === 0) {
      empty.style.display = "block";
      return;
    }

    tbody.innerHTML = items.map(inv => `
      <tr>
        <td>${inv.id}</td>
        <td>${inv.user_id}</td>
        <td><span class="fee-badge">${(parseFloat(inv.fee_pct) * 100).toFixed(2)}%</span></td>
        <td><span class="status--${inv.is_active ? 'active' : 'inactive'}" style="padding:0.2rem 0.6rem;border-radius:20px;font-size:0.7rem;font-weight:600;">${inv.is_active ? 'Activo' : 'Inactivo'}</span></td>
        <td style="font-size:0.8rem;color:var(--text-muted);">${inv.created_at ? inv.created_at.slice(0,10) : '—'}</td>
        <td>
          <button class="btn btn--ghost" style="font-size:0.75rem;padding:0.2rem 0.6rem;" onclick="openEditModal(${JSON.stringify(inv).replace(/"/g,'&quot;')})">
            Editar
          </button>
        </td>
      </tr>
    `).join("");

    table.style.display = "table";
  } catch (e) {
    loading.textContent = "Error al cargar inversores.";
  }
}

// ── Crear ────────────────────────────────────────────────────────────

function openCreateModal() {
  document.getElementById("inp-user-id").value = "";
  document.getElementById("inp-fee-pct").value  = "";
  document.getElementById("create-error").style.display = "none";
  document.getElementById("modal-create").style.display = "flex";
}

function closeCreateModal() {
  document.getElementById("modal-create").style.display = "none";
}

async function submitCreate() {
  const userId = parseInt(document.getElementById("inp-user-id").value);
  const feePct = parseFloat(document.getElementById("inp-fee-pct").value);

  if (!userId || isNaN(feePct)) {
    showError("create-error", "Completa todos los campos.");
    return;
  }

  try {
    const res  = await fetch(API, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, fee_pct: feePct / 100 }),
    });
    const json = await res.json();
    if (!res.ok) { showError("create-error", json.msg || "Error al crear."); return; }
    closeCreateModal();
    loadInvestors();
  } catch (e) {
    showError("create-error", "Error de red.");
  }
}

// ── Editar ───────────────────────────────────────────────────────────

function openEditModal(inv) {
  document.getElementById("edit-id").value        = inv.id;
  document.getElementById("edit-fee-pct").value   = (parseFloat(inv.fee_pct) * 100).toFixed(2);
  document.getElementById("edit-is-active").checked = inv.is_active;
  document.getElementById("edit-error").style.display = "none";
  document.getElementById("modal-edit").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("modal-edit").style.display = "none";
}

async function submitEdit() {
  const id      = document.getElementById("edit-id").value;
  const feePct  = parseFloat(document.getElementById("edit-fee-pct").value);
  const active  = document.getElementById("edit-is-active").checked;

  if (isNaN(feePct)) { showError("edit-error", "Fee inválido."); return; }

  try {
    const res  = await fetch(`${API}/${id}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fee_pct: feePct / 100, is_active: active }),
    });
    const json = await res.json();
    if (!res.ok) { showError("edit-error", json.msg || "Error al actualizar."); return; }
    closeEditModal();
    loadInvestors();
  } catch (e) {
    showError("edit-error", "Error de red.");
  }
}

// ── Utils ─────────────────────────────────────────────────────────────

function showError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent    = msg;
  el.style.display  = "block";
}

// Cerrar modal al click fuera
document.querySelectorAll(".modal-overlay").forEach(o => {
  o.addEventListener("click", e => { if (e.target === o) o.style.display = "none"; });
});

loadInvestors();
