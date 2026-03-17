// ======================================================================
// static/js/agent/analyze.js
//
// Lógica de la página de análisis del Agente AI.
//
// FLUJO:
// 1. Al cargar: poblar los selectores (símbolos, timeframes, estrategias,
//    cuentas, feature sets) con llamadas paralelas a la API.
// 2. Al hacer clic en "Ejecutar Análisis": llamar a POST /agent/analyze.
// 3. Mostrar el resultado completo: decision, precios, R/R, razonamiento,
//    y el detalle de cada fase (régimen, reglas, R/R check).
// ======================================================================

"use strict";

// ======================================================================
// Helpers
// ======================================================================

async function apiFetch(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();
  return json.data?.items ?? json.data ?? [];
}

function showAlert(msg, type = "error") {
  const el = document.getElementById("alert-msg");
  el.textContent = msg;
  el.className = `alert alert-${type}`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 6000);
}

function populateSelect(id, items, valueFn, labelFn, placeholder) {
  const sel = document.getElementById(id);
  sel.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach(item => {
    const opt = document.createElement("option");
    opt.value = valueFn(item);
    opt.textContent = labelFn(item);
    sel.appendChild(opt);
  });
}

// ======================================================================
// Cargar datos iniciales
// ======================================================================

async function loadSelectors() {
  try {
    const [symbols, timeframes, strategies, accounts, featureSets] = await Promise.all([
      apiFetch("/symbols?is_active=true"),
      apiFetch("/timeframes"),
      apiFetch("/api/strategies"),
      apiFetch("/accounts"),
      apiFetch("/feature-sets"),
    ]);

    populateSelect("symbol-select", symbols,
      s => s.id, s => `${s.symbol} (${s.asset_class})`, "Seleccionar símbolo");

    populateSelect("timeframe-select", timeframes,
      t => t.id, t => t.code, "Seleccionar timeframe");

    populateSelect("strategy-select", strategies,
      s => s.id, s => `${s.name} v${s.version}`, "Seleccionar estrategia");

    populateSelect("account-select", accounts,
      a => a.id, a => `${a.name} (${a.mode})`, "Seleccionar cuenta");

    populateSelect("feature-set-select", featureSets,
      f => f.id, f => `${f.name} v${f.version}`, "Seleccionar feature set");

  } catch (err) {
    showAlert("Error al cargar los selectores: " + err.message);
  }
}

// ======================================================================
// Ejecutar análisis
// ======================================================================

async function runAnalysis() {
  const symbolId     = document.getElementById("symbol-select").value;
  const timeframeId  = document.getElementById("timeframe-select").value;
  const strategyId   = document.getElementById("strategy-select").value;
  const accountId    = document.getElementById("account-select").value;
  const featureSetId = document.getElementById("feature-set-select").value;

  if (!symbolId || !timeframeId || !strategyId || !accountId || !featureSetId) {
    showAlert("Por favor selecciona todos los parámetros.", "warning");
    return;
  }

  // Mostrar spinner, ocultar resultado
  document.getElementById("result-panel").style.display = "none";
  document.getElementById("result-placeholder").style.display = "none";
  document.getElementById("analyzing-overlay").style.display = "block";
  document.getElementById("btn-analyze").disabled = true;
  document.getElementById("alert-msg").classList.add("hidden");

  try {
    const res = await fetch("/agent/analyze", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol_id:      parseInt(symbolId),
        timeframe_id:   parseInt(timeframeId),
        strategy_id:    parseInt(strategyId),
        account_id:     parseInt(accountId),
        feature_set_id: parseInt(featureSetId),
      }),
    });

    const json = await res.json();

    if (!res.ok || json.errorCode !== 0) {
      showAlert(json.msg || "Error en el análisis.");
      return;
    }

    renderResult(json.data, json.msg);

  } catch (err) {
    showAlert("Error de red: " + err.message);
  } finally {
    document.getElementById("analyzing-overlay").style.display = "none";
    document.getElementById("btn-analyze").disabled = false;
  }
}

// ======================================================================
// Renderizar resultado
// ======================================================================

function renderResult(data, msg) {
  const approved = data.decision === "APPROVED";

  // Badge de decisión
  const badge = document.getElementById("decision-badge");
  badge.textContent = approved ? "✓ APROBADA" : "✗ RECHAZADA";
  badge.className = `badge ${approved ? "badge-success" : "badge-danger"}`;

  // Precios
  const fmt = (v, d = 4) => v != null ? Number(v).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: d }) : "—";
  document.getElementById("res-entry").textContent = fmt(data.entry);
  document.getElementById("res-sl").textContent    = fmt(data.stop_loss);
  document.getElementById("res-tp").textContent    = fmt(data.take_profit);
  document.getElementById("res-size").textContent  = data.position_size != null ? `${fmt(data.position_size, 6)} uds` : "—";
  document.getElementById("res-rr").textContent    = data.rr_ratio != null ? `${Number(data.rr_ratio).toFixed(2)}x` : "—";

  // Razonamiento
  document.getElementById("res-reasoning").textContent = data.reasoning || "(sin razonamiento)";

  // Fases del análisis
  function phaseBadge(id, passed) {
    const el = document.getElementById(id);
    el.className = `badge ${passed ? "badge-success" : "badge-danger"}`;
  }
  phaseBadge("phase-regime", data.regime_check_passed);
  phaseBadge("phase-rules",  data.rules_check_passed);
  phaseBadge("phase-rr",     data.rr_check_passed);

  // Detalle de reglas
  const rulesSection = document.getElementById("rules-detail-section");
  const rulesList    = document.getElementById("rules-detail-list");

  if (data.rules_detail && data.rules_detail.length > 0) {
    rulesList.innerHTML = "";
    data.rules_detail.forEach(r => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;justify-content:space-between;align-items:center;font-size:0.8rem;padding:0.25rem 0;border-bottom:1px solid var(--border);";
      row.innerHTML = `
        <span style="color:var(--text-secondary);">${r.indicator} ${r.operator} ${r.threshold}</span>
        <span style="color:var(--text-muted);">${r.actual_value != null ? Number(r.actual_value).toFixed(4) : "N/A"}</span>
        <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}" style="font-size:0.7rem;">
          ${r.passed ? "✓ PASS" : "✗ FAIL"}
        </span>`;
      rulesList.appendChild(row);
    });
    rulesSection.style.display = "block";
  } else {
    rulesSection.style.display = "none";
  }

  // Mostrar panel
  document.getElementById("result-placeholder").style.display = "none";
  document.getElementById("result-panel").style.display = "block";

  // Actualizar iconos de Lucide
  if (window.lucide) lucide.createIcons();
}

// ======================================================================
// Init
// ======================================================================

document.addEventListener("DOMContentLoaded", () => {
  loadSelectors();
  document.getElementById("btn-analyze").addEventListener("click", runAnalysis);
  if (window.lucide) lucide.createIcons();
});
