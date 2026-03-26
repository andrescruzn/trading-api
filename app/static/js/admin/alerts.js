// admin/alerts.js — Vista admin de todas las reglas y eventos

"use strict";

document.getElementById("tabRules").addEventListener("click", () => switchTab("rules"));
document.getElementById("tabEvents").addEventListener("click", () => switchTab("events"));

function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.getElementById("tab" + cap(tab)).classList.add("active");
  document.getElementById("panelRules").style.display  = tab === "rules"  ? "" : "none";
  document.getElementById("panelEvents").style.display = tab === "events" ? "" : "none";
  if (tab === "events") loadEvents();
}

function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ======================================================================
// Rules
// ======================================================================
async function loadRules() {
  try {
    const res = await fetch("/api/alert-rules", { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : (json.data?.items || []);
    const tbody = document.getElementById("tbodyRules");
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Sin reglas.</td></tr>`;
      return;
    }
    tbody.innerHTML = items.map(r => `
      <tr>
        <td class="text-muted">${r.id}</td>
        <td><strong>${esc(r.name)}</strong></td>
        <td><span class="rule-type-badge rt--${r.rule_type}">${r.rule_type}</span></td>
        <td>${r.user_id ? `#${r.user_id}` : '<span class="text-muted">—</span>'}</td>
        <td>${r.bot_id  ? `<span class="badge">#${r.bot_id}</span>` : '<span class="text-muted">—</span>'}</td>
        <td style="font-size:0.8rem;">${renderChannels(r.channels)}</td>
        <td><span class="badge ${r.is_active ? 'badge--active' : 'badge--inactive'}">${r.is_active ? "Activa" : "Inactiva"}</span></td>
      </tr>
    `).join("");
  } catch (e) {
    document.getElementById("tbodyRules").innerHTML =
      `<tr><td colspan="7" class="text-center text-muted">Error al cargar.</td></tr>`;
  }
}

function renderChannels(channels) {
  const parts = [];
  if (channels.email)   parts.push("📧 Email");
  if (channels.telegram) parts.push("✈️ Telegram");
  if (channels.webhook) parts.push("🔗 Webhook");
  if (channels.desktop) parts.push("🖥 Desktop");
  return parts.length ? parts.join(", ") : '<span class="text-muted">Ninguno</span>';
}

// ======================================================================
// Events
// ======================================================================
async function loadEvents() {
  try {
    const res = await fetch("/api/alert-events?limit=200", { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : (json.data?.items || []);
    const tbody = document.getElementById("tbodyEvents");
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Sin eventos.</td></tr>`;
      return;
    }
    tbody.innerHTML = items.map(e => `
      <tr>
        <td class="text-muted" style="font-size:0.8rem;white-space:nowrap;">${e.ts ? new Date(e.ts).toLocaleString("es-ES") : "—"}</td>
        <td><strong>${esc(e.title)}</strong></td>
        <td><span class="rule-type-badge severity--${e.severity}">${e.severity}</span></td>
        <td><span class="rule-type-badge delivery--${e.delivery_status}">${e.delivery_status}</span></td>
        <td>${e.user_id ? `#${e.user_id}` : '<span class="text-muted">—</span>'}</td>
        <td>${e.bot_id  ? `#${e.bot_id}` : '<span class="text-muted">—</span>'}</td>
      </tr>
    `).join("");
  } catch (e) {
    document.getElementById("tbodyEvents").innerHTML =
      `<tr><td colspan="6" class="text-center text-muted">Error al cargar.</td></tr>`;
  }
}

function esc(str) {
  return String(str || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

loadRules();
if (typeof lucide !== "undefined") lucide.createIcons();
