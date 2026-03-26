// alerts/index.js — Reglas y eventos de alerta del usuario

"use strict";

// ======================================================================
// State
// ======================================================================
let editingRuleId = null;

// ======================================================================
// Tabs
// ======================================================================
document.getElementById("tabRules").addEventListener("click", () => switchTab("rules"));
document.getElementById("tabEvents").addEventListener("click", () => switchTab("events"));

function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.getElementById("tab" + cap(tab)).classList.add("active");
  document.getElementById("panelRules").style.display = tab === "rules" ? "" : "none";
  document.getElementById("panelEvents").style.display = tab === "events" ? "" : "none";
  if (tab === "events") loadEvents();
}

function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ======================================================================
// Load rules
// ======================================================================
async function loadRules() {
  try {
    const res = await fetch("/api/alert-rules", { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : (json.data?.items || []);
    renderRules(items);
  } catch (e) {
    document.getElementById("tbodyRules").innerHTML =
      `<tr><td colspan="7" class="text-center text-muted">Error al cargar reglas</td></tr>`;
  }
}

function renderRules(rules) {
  const tbody = document.getElementById("tbodyRules");
  if (!rules.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Sin reglas configuradas. Crea la primera.</td></tr>`;
    return;
  }
  tbody.innerHTML = rules.map(r => `
    <tr>
      <td><strong>${esc(r.name)}</strong></td>
      <td><span class="rule-type-badge rt--${r.rule_type}">${r.rule_type}</span></td>
      <td>${r.bot_id ? `<span class="badge">#${r.bot_id}</span>` : '<span class="text-muted">—</span>'}</td>
      <td>${renderChannels(r.channels)}</td>
      <td>
        <span class="badge ${r.is_active ? 'badge--active' : 'badge--inactive'}">
          ${r.is_active ? "Activa" : "Inactiva"}
        </span>
      </td>
      <td class="text-muted">${r.created_at ? new Date(r.created_at).toLocaleDateString("es-ES") : "—"}</td>
      <td style="text-align:right;">
        <button class="btn btn--ghost btn--xs" data-edit="${r.id}" style="padding:0.2rem 0.5rem;font-size:0.75rem;">Editar</button>
        <button class="btn btn--ghost btn--xs" data-toggle="${r.id}" data-active="${r.is_active}"
          style="padding:0.2rem 0.5rem;font-size:0.75rem;color:${r.is_active ? '#ef4444' : '#22c55e'}">
          ${r.is_active ? "Desactivar" : "Activar"}
        </button>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-edit]").forEach(btn => {
    btn.addEventListener("click", () => openEditModal(parseInt(btn.dataset.edit), rules));
  });
  tbody.querySelectorAll("[data-toggle]").forEach(btn => {
    btn.addEventListener("click", () => toggleRule(parseInt(btn.dataset.toggle), btn.dataset.active === "true"));
  });
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
// Load events
// ======================================================================
async function loadEvents() {
  try {
    const res = await fetch("/api/alert-events?limit=100", { credentials: "include" });
    const json = await res.json();
    const items = Array.isArray(json.data) ? json.data : (json.data?.items || []);
    renderEvents(items);
  } catch (e) {
    document.getElementById("tbodyEvents").innerHTML =
      `<tr><td colspan="5" class="text-center text-muted">Error al cargar historial</td></tr>`;
  }
}

function renderEvents(events) {
  const tbody = document.getElementById("tbodyEvents");
  if (!events.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Sin eventos de alerta aún.</td></tr>`;
    return;
  }
  tbody.innerHTML = events.map(e => `
    <tr>
      <td class="text-muted" style="font-size:0.8125rem;white-space:nowrap;">${e.ts ? new Date(e.ts).toLocaleString("es-ES") : "—"}</td>
      <td><strong>${esc(e.title)}</strong></td>
      <td><span class="rule-type-badge severity--${e.severity}">${e.severity}</span></td>
      <td><span class="rule-type-badge delivery--${e.delivery_status}">${e.delivery_status}</span></td>
      <td class="text-muted" style="font-size:0.8125rem;">${esc(e.message || "")}</td>
    </tr>
  `).join("");
}

// ======================================================================
// Modal: Nueva Regla
// ======================================================================
document.getElementById("btnNewRule").addEventListener("click", openCreateModal);
document.getElementById("btnCloseModal").addEventListener("click", closeModal);
document.getElementById("btnCancelModal").addEventListener("click", closeModal);
document.getElementById("modalBackdrop").addEventListener("click", closeModal);
document.getElementById("selectRuleType").addEventListener("change", updateSpecPanel);
document.getElementById("btnSaveRule").addEventListener("click", saveRule);

function openCreateModal() {
  editingRuleId = null;
  document.getElementById("modalRuleTitle").textContent = "Nueva Regla de Alerta";
  clearModal();
  showModal();
}

function openEditModal(ruleId, rules) {
  const rule = rules.find(r => r.id === ruleId);
  if (!rule) return;
  editingRuleId = ruleId;
  document.getElementById("modalRuleTitle").textContent = "Editar Regla";
  document.getElementById("inputRuleName").value = rule.name;
  document.getElementById("selectRuleType").value = rule.rule_type;
  document.getElementById("inputBotId").value = rule.bot_id || "";
  // channels
  document.getElementById("chEmail").checked = !!rule.channels.email;
  document.getElementById("chTelegram").checked = !!rule.channels.telegram;
  document.getElementById("chDesktop").checked = !!rule.channels.desktop;
  document.getElementById("inputWebhookUrl").value =
    typeof rule.channels.webhook === "string" ? rule.channels.webhook : "";
  // spec
  updateSpecPanel();
  if (rule.rule_type === "signal" && rule.rule_spec.action)
    document.getElementById("specSignalAction").value = rule.rule_spec.action;
  if (rule.rule_type === "price") {
    document.getElementById("specPriceSymbol").value = rule.rule_spec.symbol_id || "";
    document.getElementById("specPriceOp").value = rule.rule_spec.operator || "lt";
    document.getElementById("specPriceThreshold").value = rule.rule_spec.threshold || "";
  }
  if (rule.rule_type === "pnl") {
    document.getElementById("specPnlThreshold").value = rule.rule_spec.threshold || "";
    document.getElementById("specPnlPeriod").value = rule.rule_spec.period || "daily";
  }
  if (rule.rule_type === "drawdown")
    document.getElementById("specDrawdownThreshold").value = rule.rule_spec.threshold || "";
  showModal();
}

function clearModal() {
  document.getElementById("inputRuleName").value = "";
  document.getElementById("selectRuleType").value = "signal";
  document.getElementById("inputBotId").value = "";
  document.getElementById("chEmail").checked = false;
  document.getElementById("chTelegram").checked = false;
  document.getElementById("chDesktop").checked = false;
  document.getElementById("inputWebhookUrl").value = "";
  document.getElementById("ruleModalError").style.display = "none";
  updateSpecPanel();
}

function showModal() {
  document.getElementById("ruleModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeModal() {
  document.getElementById("ruleModal").classList.add("hidden");
}

function updateSpecPanel() {
  const type = document.getElementById("selectRuleType").value;
  ["signal", "price", "pnl", "drawdown", "error"].forEach(t => {
    const el = document.getElementById("spec" + cap(t));
    if (el) el.style.display = t === type ? "" : "none";
  });
}

function buildRuleSpec() {
  const type = document.getElementById("selectRuleType").value;
  if (type === "signal") {
    return { action: document.getElementById("specSignalAction").value };
  }
  if (type === "price") {
    const symId = parseInt(document.getElementById("specPriceSymbol").value);
    const threshold = parseFloat(document.getElementById("specPriceThreshold").value);
    if (!symId || isNaN(threshold)) return null;
    return { symbol_id: symId, operator: document.getElementById("specPriceOp").value, threshold };
  }
  if (type === "pnl") {
    const threshold = parseFloat(document.getElementById("specPnlThreshold").value);
    if (isNaN(threshold)) return null;
    return { threshold, period: document.getElementById("specPnlPeriod").value };
  }
  if (type === "drawdown") {
    const threshold = parseFloat(document.getElementById("specDrawdownThreshold").value);
    if (isNaN(threshold)) return null;
    return { threshold };
  }
  return {};
}

async function saveRule() {
  const name = document.getElementById("inputRuleName").value.trim();
  const ruleType = document.getElementById("selectRuleType").value;
  const botIdRaw = document.getElementById("inputBotId").value.trim();
  const errEl = document.getElementById("ruleModalError");

  if (!name) { showErr(errEl, "El nombre es obligatorio."); return; }
  const ruleSpec = buildRuleSpec();
  if (ruleSpec === null) { showErr(errEl, "Completa los campos del spec de la regla."); return; }

  const webhookUrl = document.getElementById("inputWebhookUrl").value.trim();
  const channels = {
    email: document.getElementById("chEmail").checked,
    telegram: document.getElementById("chTelegram").checked,
    desktop: document.getElementById("chDesktop").checked,
    webhook: webhookUrl || false,
  };

  const body = {
    name, rule_type: ruleType, rule_spec: ruleSpec, channels,
    bot_id: botIdRaw ? parseInt(botIdRaw) : null,
  };

  errEl.style.display = "none";
  document.getElementById("btnSaveRule").disabled = true;

  try {
    let res;
    if (editingRuleId) {
      const patch = { name, rule_spec: ruleSpec, channels };
      res = await fetch(`/api/alert-rules/${editingRuleId}`, {
        method: "PUT", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
    } else {
      res = await fetch("/api/alert-rules", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    const json = await res.json();
    if (json.errorCode >= 400) { showErr(errEl, json.msg || "Error al guardar."); return; }
    closeModal();
    loadRules();
  } catch (e) {
    showErr(errEl, "Error de red.");
  } finally {
    document.getElementById("btnSaveRule").disabled = false;
  }
}

async function toggleRule(ruleId, isActive) {
  try {
    await fetch(`/api/alert-rules/${ruleId}`, {
      method: "PUT", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: !isActive }),
    });
    loadRules();
  } catch (e) {}
}

// ======================================================================
// Utils
// ======================================================================
function showErr(el, msg) {
  el.textContent = msg;
  el.style.display = "block";
}

function esc(str) {
  return String(str || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ======================================================================
// Init
// ======================================================================
loadRules();
if (typeof lucide !== "undefined") lucide.createIcons();
