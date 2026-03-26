"use strict";

// ======================================================================
// investor/dashboard.js
// Dashboard del inversor — equity, PnL y fees
// ======================================================================

let _investorId  = null;
let _feePct      = null;

// ── Init ──────────────────────────────────────────────────────────────

async function init() {
  try {
    // Obtener el investor_id del usuario actual via /users/me + /api/investors
    const meRes  = await fetch("/users/me", { credentials: "include" });
    const meJson = await meRes.json();
    const userId = meJson.data?.id;
    if (!userId) return;

    // Buscar perfil de inversor por user_id
    const invRes  = await fetch("/api/investors", { credentials: "include" });
    const invJson = await invRes.json();
    const investors = Array.isArray(invJson.data) ? invJson.data : [];
    const mine = investors.find(i => i.user_id === userId);
    if (!mine) {
      document.getElementById("dashboard-loading").textContent = "No tienes perfil de inversor registrado.";
      return;
    }
    _investorId = mine.id;
    _feePct     = mine.fee_pct;

    // Cargar cuentas gestionadas del inversor
    const acRes  = await fetch(`/api/managed-accounts`, { credentials: "include" });
    const acJson = await acRes.json();
    const accounts = Array.isArray(acJson.data) ? acJson.data : [];

    const sel = document.getElementById("sel-account");
    accounts.forEach(a => {
      const opt = document.createElement("option");
      opt.value        = a.id;
      opt.textContent  = `${a.name}`;
      opt.dataset.info = JSON.stringify(a);
      sel.appendChild(opt);
    });

    if (accounts.length === 1) {
      sel.selectedIndex = 1;
      loadDashboard();
    }
  } catch (e) {
    document.getElementById("dashboard-loading").textContent = "Error al cargar.";
  }
}

// ── Cargar Dashboard ──────────────────────────────────────────────────

async function loadDashboard() {
  const sel = document.getElementById("sel-account");
  if (!sel.value) return;

  const accountId = parseInt(sel.value);
  const opt       = sel.options[sel.selectedIndex];
  const account   = JSON.parse(opt.dataset.info || "{}");

  document.getElementById("dashboard-loading").style.display = "none";

  // KPIs de la cuenta
  document.getElementById("kpi-section").style.display = "block";
  document.getElementById("kpi-initial").textContent   = "$" + fmtNum(account.initial_capital);
  document.getElementById("kpi-hwm").textContent       = "$" + fmtNum(account.high_water_mark);

  // Cargar períodos en paralelo con fees
  const [periodsRes, feesRes] = await Promise.all([
    fetch(`/api/billing-periods?managed_account_id=${accountId}`, { credentials: "include" }),
    fetch(`/api/fee-transactions?managed_account_id=${accountId}`, { credentials: "include" }),
  ]);

  const periodsJson = await periodsRes.json();
  const feesJson    = await feesRes.json();

  const periods = Array.isArray(periodsJson.data) ? periodsJson.data : [];
  const fees    = Array.isArray(feesJson.data)    ? feesJson.data    : [];

  // Calcular KPIs agregados
  let totalNetPnl  = 0;
  let totalFeePaid = 0;
  periods.filter(p => p.status === "closed").forEach(p => {
    if (p.net_pnl    !== null) totalNetPnl  += parseFloat(p.net_pnl);
    if (p.fee_amount !== null) totalFeePaid += parseFloat(p.fee_amount);
  });

  const netPnlEl = document.getElementById("kpi-net-pnl");
  netPnlEl.textContent = "$" + fmtNum(totalNetPnl);
  netPnlEl.className   = "kpi-card__value " + (totalNetPnl >= 0 ? "positive" : "negative");

  document.getElementById("kpi-total-fees").textContent = "$" + fmtNum(totalFeePaid);
  document.getElementById("kpi-fee-pct").textContent    = _feePct !== null ? (parseFloat(_feePct) * 100).toFixed(2) + "%" : "—";

  // Tabla de períodos
  renderPeriods(periods);
  renderFees(fees);

  document.getElementById("periods-section").style.display = "block";
  document.getElementById("fees-section").style.display    = "block";
}

function renderPeriods(periods) {
  const tbody = document.getElementById("periods-body");
  const empty = document.getElementById("periods-empty");

  if (periods.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";
  tbody.innerHTML = periods.map((p, i) => {
    const grossPnl = p.gross_pnl !== null ? parseFloat(p.gross_pnl) : null;
    const netPnl   = p.net_pnl   !== null ? parseFloat(p.net_pnl)   : null;
    return `
      <tr>
        <td style="color:var(--text-muted);">Período ${periods.length - i}</td>
        <td style="font-size:0.8rem;">${p.start_ts ? p.start_ts.slice(0,10) : '—'}</td>
        <td style="font-size:0.8rem;">${p.end_ts ? p.end_ts.slice(0,10) : '—'}</td>
        <td>$${fmtNum(p.opening_equity)}</td>
        <td>${p.closing_equity !== null ? "$"+fmtNum(p.closing_equity) : "—"}</td>
        <td class="${pnlClass(grossPnl)}">${grossPnl !== null ? "$"+fmtNum(grossPnl) : "—"}</td>
        <td style="color:#ef4444;">${p.fee_amount !== null ? "$"+fmtNum(p.fee_amount) : "—"}</td>
        <td class="${pnlClass(netPnl)}">${netPnl !== null ? "$"+fmtNum(netPnl) : "—"}</td>
        <td><span class="status--${p.status}">${p.status === 'open' ? 'Abierto' : 'Cerrado'}</span></td>
      </tr>
    `;
  }).join("");
}

function renderFees(fees) {
  const tbody = document.getElementById("fees-body");
  const empty = document.getElementById("fees-empty");

  if (fees.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";
  tbody.innerHTML = fees.map(tx => `
    <tr>
      <td>${tx.billing_period_id}</td>
      <td style="font-weight:600;color:#ef4444;">$${fmtNum(tx.amount)}</td>
      <td><span class="fee--${tx.status}">${tx.status}</span></td>
      <td style="font-size:0.8rem;">${tx.charged_at ? tx.charged_at.slice(0,10) : '—'}</td>
      <td style="font-size:0.8rem;">${tx.created_at ? tx.created_at.slice(0,10) : '—'}</td>
    </tr>
  `).join("");
}

// ── Utils ─────────────────────────────────────────────────────────────

function fmtNum(v) {
  return parseFloat(v || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pnlClass(v) {
  if (v === null) return "";
  return v >= 0 ? "pnl--positive" : "pnl--negative";
}

init();
