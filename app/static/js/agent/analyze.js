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

function setSelectError(id, label) {
  const sel = document.getElementById(id);
  sel.innerHTML = `<option value="">Error al cargar ${label}</option>`;
}

async function loadSelectors() {
  const [symbols, timeframes, strategies, accounts, featureSets] = await Promise.allSettled([
    apiFetch("/symbols?is_active=true"),
    apiFetch("/timeframes"),
    apiFetch("/api/strategies"),
    apiFetch("/accounts"),
    apiFetch("/feature-sets"),
  ]);

  if (symbols.status === "fulfilled") {
    populateSelect("symbol-select", symbols.value,
      s => s.id, s => `${s.symbol} (${s.asset_class})`, "Seleccionar símbolo");
  } else {
    setSelectError("symbol-select", "símbolos");
    showAlert("Error cargando símbolos: " + symbols.reason?.message);
  }

  if (timeframes.status === "fulfilled") {
    populateSelect("timeframe-select", timeframes.value,
      t => t.id, t => t.code, "Seleccionar timeframe");
  } else {
    setSelectError("timeframe-select", "timeframes");
  }

  if (strategies.status === "fulfilled") {
    populateSelect("strategy-select", strategies.value,
      s => s.id, s => `${s.name} v${s.version}`, "Seleccionar estrategia");
  } else {
    setSelectError("strategy-select", "estrategias");
  }

  if (accounts.status === "fulfilled") {
    populateSelect("account-select", accounts.value,
      a => a.id, a => `${a.name} (${a.mode})`, "Seleccionar cuenta");
  } else {
    setSelectError("account-select", "cuentas");
  }

  if (featureSets.status === "fulfilled") {
    populateSelect("feature-set-select", featureSets.value,
      f => f.id, f => `${f.name} v${f.version}`, "Seleccionar feature set");
  } else {
    setSelectError("feature-set-select", "feature sets");
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

    if (!res.ok || json.errorCode >= 400) {
      showAlert(json.msg || "Error en el análisis.");
      return;
    }

    renderResult(json.data);

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

function renderResult(data) {
  const approved = data.decision === "APPROVED";

  // Decisión banner
  const banner = document.getElementById("decision-banner");
  banner.className = `decision-banner ${approved ? "decision-banner--approved" : "decision-banner--rejected"}`;
  document.getElementById("decision-text").textContent = approved ? "✓ APROBADA" : "✗ RECHAZADA";

  // Precios
  const fmt = (v, d = 4) => v != null
    ? Number(v).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: d })
    : "—";
  document.getElementById("res-entry").textContent = fmt(data.entry);
  document.getElementById("res-sl").textContent    = fmt(data.stop_loss);
  document.getElementById("res-tp").textContent    = fmt(data.take_profit);
  document.getElementById("res-size").textContent  = data.position_size != null
    ? `${fmt(data.position_size, 6)} uds` : "—";
  document.getElementById("res-rr").textContent    = data.rr_ratio != null
    ? `${Number(data.rr_ratio).toFixed(2)}×` : "—";

  // Razonamiento
  document.getElementById("res-reasoning").textContent = data.reasoning || "(sin razonamiento)";

  // Fases
  function setPhase(id, passed) {
    const el = document.getElementById(id);
    el.className = `phase-chip ${passed ? "phase-chip--pass" : "phase-chip--fail"}`;
  }
  setPhase("phase-regime", data.regime_check_passed);
  setPhase("phase-rules",  data.rules_check_passed);
  setPhase("phase-rr",     data.rr_check_passed);

  // Detalle de reglas
  const rulesSection = document.getElementById("rules-detail-section");
  const rulesList    = document.getElementById("rules-detail-list");

  if (data.rules_detail && data.rules_detail.length > 0) {
    rulesList.innerHTML = "";
    data.rules_detail.forEach(r => {
      const pass = r.passed;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color:var(--text-secondary);font-family:var(--font-mono);font-size:0.78rem;">
          ${r.indicator} <span style="color:var(--text-muted);">${r.operator}</span> ${r.threshold}
        </td>
        <td style="color:var(--text-muted);font-family:var(--font-mono);font-size:0.78rem;">
          ${r.actual_value != null ? Number(r.actual_value).toFixed(4) : "N/A"}
        </td>
        <td>
          <span style="
            font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
            color:${pass ? "var(--success)" : "var(--error)"};
          ">${pass ? "✓ PASS" : "✗ FAIL"}</span>
        </td>`;
      rulesList.appendChild(tr);
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
