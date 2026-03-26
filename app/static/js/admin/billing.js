"use strict";

// ======================================================================
// admin/billing.js
// Gestión de períodos de facturación y performance fees
// ======================================================================

let _currentAccountId = null;
let _currentPeriods   = [];

// ── Init: cargar lista de cuentas gestionadas ─────────────────────────

async function initAccountSelector() {
  try {
    const res  = await fetch("/api/managed-accounts", { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : [];
    const sel = document.getElementById("sel-managed-account");
    items.forEach(a => {
      const opt = document.createElement("option");
      opt.value       = a.id;
      opt.textContent = `#${a.id} — ${a.name} (Inv:${a.investor_id})`;
      opt.dataset.hwm = a.high_water_mark;
      sel.appendChild(opt);
    });
  } catch (e) {}
}

function loadData() {
  const sel = document.getElementById("sel-managed-account");
  _currentAccountId = sel.value ? parseInt(sel.value) : null;

  // Mostrar HWM
  const hwmDisplay = document.getElementById("hwm-display");
  if (_currentAccountId) {
    const opt = sel.options[sel.selectedIndex];
    document.getElementById("hwm-value").textContent =
      "$" + parseFloat(opt.dataset.hwm || "0").toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2});
    hwmDisplay.style.display = "inline";
  } else {
    hwmDisplay.style.display = "none";
  }

  if (document.getElementById("tab-periods").style.display !== "none") loadPeriods();
  else loadFees();
}

// ── Tabs ──────────────────────────────────────────────────────────────

function switchTab(tab, btn) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("tab-periods").style.display = tab === "periods" ? "block" : "none";
  document.getElementById("tab-fees").style.display    = tab === "fees"    ? "block" : "none";
  if (tab === "periods") loadPeriods();
  else loadFees();
}

// ── Períodos ──────────────────────────────────────────────────────────

async function loadPeriods() {
  if (!_currentAccountId) return;
  const loading = document.getElementById("periods-loading");
  const table   = document.getElementById("periods-table");
  const empty   = document.getElementById("periods-empty");
  const tbody   = document.getElementById("periods-body");

  loading.style.display = "block";
  table.style.display   = "none";
  empty.style.display   = "none";

  try {
    const res  = await fetch(`/api/billing-periods?managed_account_id=${_currentAccountId}`, { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : [];
    _currentPeriods = items;

    loading.style.display = "none";

    if (items.length === 0) { empty.style.display = "block"; empty.textContent = "Sin períodos para esta cuenta."; return; }

    tbody.innerHTML = items.map(p => {
      const grossPnl = p.gross_pnl !== null ? parseFloat(p.gross_pnl) : null;
      const netPnl   = p.net_pnl   !== null ? parseFloat(p.net_pnl)   : null;
      const pnlClass = v => v === null ? "" : v >= 0 ? "pnl--positive" : "pnl--negative";
      const fmt = v => v !== null ? "$" + parseFloat(v).toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2}) : "—";
      const closeBtn = p.status === "open"
        ? `<button class="btn btn--danger" style="font-size:0.75rem;padding:0.2rem 0.6rem;" onclick="openClosePeriodModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">Cerrar</button>`
        : "";

      return `
        <tr>
          <td>${p.id}</td>
          <td style="font-size:0.8rem;">${p.start_ts ? p.start_ts.slice(0,10) : '—'}</td>
          <td style="font-size:0.8rem;">${p.end_ts ? p.end_ts.slice(0,10) : '—'}</td>
          <td>${fmt(p.opening_equity)}</td>
          <td>${fmt(p.closing_equity)}</td>
          <td class="${pnlClass(grossPnl)}">${fmt(p.gross_pnl)}</td>
          <td>${p.fee_pct ? (parseFloat(p.fee_pct)*100).toFixed(1)+"%" : "—"}</td>
          <td>${fmt(p.fee_amount)}</td>
          <td class="${pnlClass(netPnl)}">${fmt(p.net_pnl)}</td>
          <td><span class="status--${p.status}">${p.status === 'open' ? 'Abierto' : 'Cerrado'}</span></td>
          <td>${closeBtn}</td>
        </tr>
      `;
    }).join("");

    table.style.display = "table";
  } catch (e) {
    loading.textContent = "Error al cargar períodos.";
  }
}

// ── Fees ──────────────────────────────────────────────────────────────

async function loadFees() {
  if (!_currentAccountId) return;
  const loading = document.getElementById("fees-loading");
  const table   = document.getElementById("fees-table");
  const empty   = document.getElementById("fees-empty");
  const tbody   = document.getElementById("fees-body");

  loading.style.display = "block";
  table.style.display   = "none";
  empty.style.display   = "none";

  try {
    const res  = await fetch(`/api/fee-transactions?managed_account_id=${_currentAccountId}`, { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : [];

    loading.style.display = "none";

    if (items.length === 0) { empty.style.display = "block"; empty.textContent = "Sin transacciones de fee."; return; }

    tbody.innerHTML = items.map(tx => `
      <tr>
        <td>${tx.id}</td>
        <td>${tx.billing_period_id}</td>
        <td style="font-weight:600;color:#ef4444;">$${parseFloat(tx.amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
        <td><span class="fee--${tx.status}">${tx.status}</span></td>
        <td style="font-size:0.8rem;">${tx.charged_at ? tx.charged_at.slice(0,10) : '—'}</td>
        <td style="font-size:0.8rem;color:var(--text-muted);">${tx.notes || '—'}</td>
        <td style="font-size:0.8rem;">${tx.created_at ? tx.created_at.slice(0,10) : '—'}</td>
      </tr>
    `).join("");

    table.style.display = "table";
  } catch (e) {
    loading.textContent = "Error al cargar fees.";
  }
}

// ── Abrir Período ─────────────────────────────────────────────────────

function openOpenPeriodModal() {
  if (!_currentAccountId) { alert("Selecciona una cuenta gestionada primero."); return; }
  document.getElementById("inp-opening-equity").value = "";
  document.getElementById("open-period-error").style.display = "none";
  document.getElementById("modal-open-period").style.display = "flex";
}

function closeOpenPeriodModal() {
  document.getElementById("modal-open-period").style.display = "none";
}

async function submitOpenPeriod() {
  const equity = parseFloat(document.getElementById("inp-opening-equity").value);
  if (isNaN(equity) || equity < 0) { showError("open-period-error", "Ingresa un equity válido."); return; }

  try {
    const res  = await fetch("/api/billing-periods/open", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ managed_account_id: _currentAccountId, opening_equity: equity }),
    });
    const json = await res.json();
    if (!res.ok) { showError("open-period-error", json.msg || "Error."); return; }
    closeOpenPeriodModal();
    loadPeriods();
  } catch (e) {
    showError("open-period-error", "Error de red.");
  }
}

// ── Cerrar Período ────────────────────────────────────────────────────

function openClosePeriodModal(period) {
  document.getElementById("close-period-id").value      = period.id;
  document.getElementById("inp-closing-equity").value   = "";
  document.getElementById("close-period-error").style.display = "none";
  document.getElementById("preview-opening").textContent  = "$" + parseFloat(period.opening_equity).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
  document.getElementById("preview-fee-pct").textContent  = (parseFloat(period.fee_pct)*100).toFixed(1) + "%";

  // HWM del selector
  const sel = document.getElementById("sel-managed-account");
  const opt = sel.options[sel.selectedIndex];
  document.getElementById("preview-hwm").textContent = "$" + parseFloat(opt.dataset.hwm||"0").toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
  document.getElementById("close-period-preview").style.display = "block";
  document.getElementById("modal-close-period").style.display = "flex";
}

function closeClosePeriodModal() {
  document.getElementById("modal-close-period").style.display = "none";
}

async function submitClosePeriod() {
  const periodId = document.getElementById("close-period-id").value;
  const equity   = parseFloat(document.getElementById("inp-closing-equity").value);
  if (isNaN(equity) || equity < 0) { showError("close-period-error", "Ingresa un equity válido."); return; }

  try {
    const res  = await fetch(`/api/billing-periods/${periodId}/close`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ closing_equity: equity }),
    });
    const json = await res.json();
    if (!res.ok) { showError("close-period-error", json.msg || "Error."); return; }
    closeClosePeriodModal();
    loadPeriods();

    // Refresh HWM en el selector si cambió
    const sel = document.getElementById("sel-managed-account");
    const opt = sel.options[sel.selectedIndex];
    if (json.data && json.data.gross_pnl !== null && parseFloat(json.data.gross_pnl) > 0) {
      opt.dataset.hwm = json.data.closing_equity;
      document.getElementById("hwm-value").textContent =
        "$" + parseFloat(json.data.closing_equity).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
    }
  } catch (e) {
    showError("close-period-error", "Error de red.");
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

initAccountSelector();
