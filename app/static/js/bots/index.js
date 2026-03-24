// ======================================================================
// static/js/bots/index.js
//
// Panel de bots del usuario:
// - Lista bots de una cuenta
// - Crear bot (con selects dinámicos de cuenta, símbolo, timeframe,
//   estrategia, feature_set)
// - Controles de estado: start / stop / pause
// - Panel de signals por bot
// - Generar señal manualmente
// ======================================================================

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Estado local
  // -----------------------------------------------------------------------
  let allBots    = [];
  let activeBotId = null;      // bot cuyas signals se están mostrando
  let generating  = false;

  // -----------------------------------------------------------------------
  // Helpers UI
  // -----------------------------------------------------------------------
  const $ = id => document.getElementById(id);

  function showAlert(msg, type = "error") {
    const el = $("alert-msg");
    el.textContent = msg;
    el.className = `alert alert--${type}`;
    el.classList.remove("hidden");
    setTimeout(() => el.classList.add("hidden"), 5000);
  }

  function statusBadge(status) {
    const map = {
      running: { color: "#22c55e", label: "Running" },
      stopped: { color: "#6b7280", label: "Stopped" },
      paused:  { color: "#f59e0b", label: "Paused"  },
      error:   { color: "#ef4444", label: "Error"   },
    };
    const s = map[status] || { color: "#6b7280", label: status };
    return `<span style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.75rem;">
      <span style="width:7px;height:7px;border-radius:50%;background:${s.color};"></span>
      ${s.label}
    </span>`;
  }

  function modeBadge(mode) {
    const color = mode === "live" ? "#ef4444" : "#3b82f6";
    return `<span style="font-size:0.7rem;padding:0.15rem 0.5rem;border-radius:4px;
      background:${color}22;color:${color};font-weight:600;text-transform:uppercase;">
      ${mode}</span>`;
  }

  function actionBadge(action, approved) {
    if (!approved) {
      return `<span style="font-size:0.7rem;padding:0.15rem 0.5rem;border-radius:4px;
        background:#ef444422;color:#ef4444;font-weight:600;">RECHAZADA</span>`;
    }
    const map = {
      buy:  { bg: "#22c55e22", color: "#22c55e", label: "BUY"  },
      sell: { bg: "#ef444422", color: "#ef4444", label: "SELL" },
      hold: { bg: "#6b728022", color: "#9ca3af", label: "HOLD" },
    };
    const s = map[action] || { bg: "#6b728022", color: "#9ca3af", label: action.toUpperCase() };
    return `<span style="font-size:0.7rem;padding:0.15rem 0.5rem;border-radius:4px;
      background:${s.bg};color:${s.color};font-weight:700;">${s.label}</span>`;
  }

  function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
  }

  function fmtPrice(val) {
    if (val == null) return "—";
    return parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 8 });
  }

  // -----------------------------------------------------------------------
  // Cargar selects del formulario de creación
  // -----------------------------------------------------------------------
  async function loadFormSelects() {
    const [accsRes, symsRes, tfsRes, stratsRes, fsRes] = await Promise.all([
      fetch("/accounts"),
      fetch("/symbols"),
      fetch("/timeframes"),
      fetch("/api/strategies"),
      fetch("/feature-sets"),
    ]);
    const [accs, syms, tfs, strats, fsets] = await Promise.all([
      accsRes.json(), symsRes.json(), tfsRes.json(), stratsRes.json(), fsRes.json(),
    ]);

    function populate(selectId, items, labelFn, valueFn) {
      const sel = $(selectId);
      sel.innerHTML = `<option value="">Seleccionar...</option>`;
      (items.data?.items || items.data || []).forEach(item => {
        const opt = document.createElement("option");
        opt.value = valueFn(item);
        opt.textContent = labelFn(item);
        sel.appendChild(opt);
      });
    }

    populate("f-account",     accs,   a => `${a.name} (${a.mode})`,         a => a.id);
    populate("f-symbol",      syms,   s => `${s.symbol} — ${s.asset_class}`, s => s.id);
    populate("f-timeframe",   tfs,    t => t.code,                           t => t.id);
    populate("f-strategy",    strats, s => `${s.name} v${s.version}`,       s => s.id);
    populate("f-feature-set", fsets,  f => `${f.name} v${f.version}`,       f => f.id);
  }

  // -----------------------------------------------------------------------
  // Cargar bots
  // -----------------------------------------------------------------------
  async function loadBots(accountId) {
    $("table-loading").classList.remove("hidden");
    $("table-wrapper").classList.add("hidden");
    $("empty-state").classList.add("hidden");

    const url = accountId ? `/api/bots?account_id=${accountId}` : "/api/bots";
    const res  = await fetch(url);
    const json = await res.json();

    $("table-loading").classList.add("hidden");

    allBots = json.data?.items || json.data || [];

    if (!allBots.length) {
      $("empty-state").classList.remove("hidden");
      return;
    }

    renderBotsTable(allBots);
    $("table-wrapper").classList.remove("hidden");
  }

  function renderBotsTable(bots) {
    const tbody = $("bots-tbody");
    tbody.innerHTML = "";

    bots.forEach(b => {
      const tr = document.createElement("tr");
      const riskPct = b.risk_params?.risk_pct != null
        ? (parseFloat(b.risk_params.risk_pct) * 100).toFixed(1) + "%"
        : "—";

      tr.innerHTML = `
        <td>${b.id}</td>
        <td>${statusBadge(b.status)}</td>
        <td>${modeBadge(b.mode)}</td>
        <td>${b.account_id ?? "—"}</td>
        <td>${b.symbol_id}</td>
        <td>${b.timeframe_id}</td>
        <td>${b.strategy_id}</td>
        <td>${riskPct}</td>
        <td>${fmtDate(b.created_at)}</td>
        <td>
          <div style="display:flex;gap:0.3rem;flex-wrap:wrap;">
            ${b.status === "stopped" ? `<button class="btn btn--primary btn-start"
              data-id="${b.id}" style="padding:0.25rem 0.6rem;font-size:0.7rem;width:auto;">
              ▶ Start</button>` : ""}
            ${b.status === "running" ? `<button class="btn btn--secondary btn-pause"
              data-id="${b.id}" style="padding:0.25rem 0.6rem;font-size:0.7rem;width:auto;">
              ⏸ Pause</button>` : ""}
            ${b.status !== "stopped" ? `<button class="btn btn--secondary btn-stop"
              data-id="${b.id}" style="padding:0.25rem 0.6rem;font-size:0.7rem;width:auto;
              color:#ef4444;border-color:#ef444444;">⏹ Stop</button>` : ""}
            <button class="btn btn--secondary btn-signals"
              data-id="${b.id}" style="padding:0.25rem 0.6rem;font-size:0.7rem;width:auto;">
              ⚡ Signals</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Event delegation
    tbody.querySelectorAll(".btn-start").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "start")));
    tbody.querySelectorAll(".btn-pause").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "pause")));
    tbody.querySelectorAll(".btn-stop").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "stop")));
    tbody.querySelectorAll(".btn-signals").forEach(btn =>
      btn.addEventListener("click", () => openSignalsPanel(+btn.dataset.id)));
  }

  // -----------------------------------------------------------------------
  // Cambio de estado
  // -----------------------------------------------------------------------
  async function changeStatus(botId, action) {
    const res  = await fetch(`/api/bots/${botId}/${action}`, { method: "POST" });
    const json = await res.json();

    if (!res.ok) {
      showAlert(json.msg || "Error al cambiar el estado del bot.");
      return;
    }

    showAlert(`Bot ${action === "start" ? "iniciado" : action === "pause" ? "pausado" : "detenido"} correctamente.`, "success");
    // Recargar tabla
    const accountId = $("f-account")?.value || null;
    await loadBots(accountId ? +accountId : undefined);
  }

  // -----------------------------------------------------------------------
  // Panel de Signals
  // -----------------------------------------------------------------------
  async function openSignalsPanel(botId) {
    activeBotId = botId;
    $("signals-panel").classList.remove("hidden");
    $("signals-bot-label").textContent = `#${botId}`;
    await loadSignals(botId);
    $("signals-panel").scrollIntoView({ behavior: "smooth" });
  }

  async function loadSignals(botId) {
    $("signals-loading").classList.remove("hidden");
    $("signals-wrapper").classList.add("hidden");
    $("signals-empty").classList.add("hidden");

    const res  = await fetch(`/api/signals?bot_id=${botId}&limit=20`);
    const json = await res.json();

    $("signals-loading").classList.add("hidden");

    const signals = json.data?.items || json.data || [];

    if (!signals.length) {
      $("signals-empty").classList.remove("hidden");
      return;
    }

    renderSignalsTable(signals);
    $("signals-wrapper").classList.remove("hidden");
  }

  function renderSignalsTable(signals) {
    const tbody = $("signals-tbody");
    tbody.innerHTML = "";

    signals.forEach(s => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${s.id}</td>
        <td>${actionBadge(s.action, s.approved)}</td>
        <td>${s.approved
          ? `<span style="color:#22c55e;font-size:0.75rem;">✓ Sí</span>`
          : `<span style="color:#ef4444;font-size:0.75rem;">✗ No</span>`}</td>
        <td>${fmtPrice(s.entry_price)}</td>
        <td>${fmtPrice(s.stop_loss)}</td>
        <td>${fmtPrice(s.take_profit)}</td>
        <td>${s.rr_ratio != null ? parseFloat(s.rr_ratio).toFixed(2) + "x" : "—"}</td>
        <td>${s.confidence != null ? (parseFloat(s.confidence) * 100).toFixed(0) + "%" : "—"}</td>
        <td style="font-size:0.75rem;">${fmtDate(s.ts)}</td>
        <td>
          <button class="btn btn--secondary btn-signal-detail"
            data-signal='${JSON.stringify(s).replace(/'/g, "&#39;")}'
            style="padding:0.2rem 0.5rem;font-size:0.7rem;width:auto;">
            Ver
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".btn-signal-detail").forEach(btn =>
      btn.addEventListener("click", () => openSignalDetail(JSON.parse(btn.dataset.signal))));
  }

  // -----------------------------------------------------------------------
  // Modal detalle de señal
  // -----------------------------------------------------------------------
  function openSignalDetail(signal) {
    const reasons = signal.reasons || {};
    const content = $("signal-detail-content");

    content.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1rem;">
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Acción</p>
          <p>${actionBadge(signal.action, signal.approved)}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Confianza</p>
          <p style="font-weight:600;">${signal.confidence != null ? (parseFloat(signal.confidence)*100).toFixed(0)+"%" : "—"}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Entry</p>
          <p style="font-weight:600;">${fmtPrice(signal.entry_price)}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Stop Loss</p>
          <p style="font-weight:600;color:#ef4444;">${fmtPrice(signal.stop_loss)}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Take Profit</p>
          <p style="font-weight:600;color:#22c55e;">${fmtPrice(signal.take_profit)}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">R/R Ratio</p>
          <p style="font-weight:600;">${signal.rr_ratio != null ? parseFloat(signal.rr_ratio).toFixed(2)+"x" : "—"}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Position Size</p>
          <p style="font-weight:600;">${fmtPrice(signal.position_size)}</p>
        </div>
        <div>
          <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.2rem;">Timestamp</p>
          <p style="font-weight:600;">${fmtDate(signal.ts)}</p>
        </div>
      </div>
      ${reasons.reasoning ? `
      <div style="margin-bottom:0.75rem;">
        <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.3rem;">Razonamiento del Agente</p>
        <p style="font-size:0.8125rem;line-height:1.5;">${reasons.reasoning}</p>
      </div>` : ""}
      ${reasons.rejection_reason ? `
      <div style="margin-bottom:0.75rem;">
        <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.3rem;">Razón de rechazo</p>
        <p style="font-size:0.8125rem;color:#ef4444;">${reasons.rejection_reason}</p>
      </div>` : ""}
      <div>
        <p class="text-muted" style="font-size:0.75rem;margin-bottom:0.3rem;">JSON completo (reasons)</p>
        <pre style="background:var(--surface-2,#1a1a2e);border-radius:6px;padding:0.75rem;
          font-size:0.7rem;overflow:auto;max-height:160px;color:var(--text-secondary,#b0b0c0);
          white-space:pre-wrap;word-break:break-all;">${JSON.stringify(reasons, null, 2)}</pre>
      </div>
    `;

    $("modal-signal").classList.remove("hidden");
  }

  // -----------------------------------------------------------------------
  // Generar señal
  // -----------------------------------------------------------------------
  async function generateSignal() {
    if (!activeBotId || generating) return;
    generating = true;

    const btn = $("btn-generate-signal");
    btn.disabled = true;
    btn.textContent = "Generando...";

    const res  = await fetch("/api/signals/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bot_id: activeBotId }),
    });
    const json = await res.json();

    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="zap" style="width:12px;height:12px;margin-right:0.25rem;"></i> Generar Señal`;
    generating = false;

    if (!res.ok) {
      showAlert(json.msg || "Error al generar la señal.");
      return;
    }

    showAlert("Señal generada correctamente.", "success");
    await loadSignals(activeBotId);

    // Re-inicializar iconos Lucide en el nuevo contenido
    if (window.lucide) lucide.createIcons();
  }

  // -----------------------------------------------------------------------
  // Modal crear bot
  // -----------------------------------------------------------------------
  function openCreateModal() {
    $("form-create-bot").reset();
    $("create-error").classList.add("hidden");
    $("modal-create").classList.remove("hidden");
    loadFormSelects();
  }

  async function submitCreateBot(e) {
    e.preventDefault();

    const accountId   = +$("f-account").value;
    const symbolId    = +$("f-symbol").value;
    const timeframeId = +$("f-timeframe").value;
    const strategyId  = +$("f-strategy").value;
    const featureSetId= +$("f-feature-set").value;
    const mode        = $("f-mode").value;
    const riskPct     = parseFloat($("f-risk-pct").value);

    if (!accountId || !symbolId || !timeframeId || !strategyId || !featureSetId) {
      $("create-error").textContent = "Por favor completa todos los campos.";
      $("create-error").classList.remove("hidden");
      return;
    }

    const btn = $("btn-create-submit");
    btn.disabled = true;
    btn.textContent = "Creando...";

    const res = await fetch("/api/bots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        strategy_id:    strategyId,
        symbol_id:      symbolId,
        timeframe_id:   timeframeId,
        account_id:     accountId,
        feature_set_id: featureSetId,
        mode,
        risk_params: { risk_pct: riskPct },
      }),
    });
    const json = await res.json();

    btn.disabled = false;
    btn.textContent = "Crear Bot";

    if (!res.ok) {
      $("create-error").textContent = json.msg || "Error al crear el bot.";
      $("create-error").classList.remove("hidden");
      return;
    }

    $("modal-create").classList.add("hidden");
    showAlert("Bot creado exitosamente.", "success");
    await loadBots(accountId);
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", async () => {
    // Cargar bots (sin filtro de cuenta — el backend requerirá account_id para no-admin)
    // Para simplificar la UX, cargamos el primer account del usuario
    const accsRes = await fetch("/accounts");
    const accsJson = await accsRes.json();
    const accounts = accsJson.data?.items || accsJson.data || [];

    if (accounts.length) {
      await loadBots(accounts[0].id);
    } else {
      $("table-loading").classList.add("hidden");
      $("empty-state").classList.remove("hidden");
    }

    // Botones modal crear
    $("btn-new-bot").addEventListener("click", openCreateModal);
    $("btn-create-cancel").addEventListener("click", () => $("modal-create").classList.add("hidden"));
    $("modal-create").querySelector(".modal__backdrop").addEventListener("click", () =>
      $("modal-create").classList.add("hidden"));
    $("form-create-bot").addEventListener("submit", submitCreateBot);

    // Botones signals panel
    $("btn-close-signals").addEventListener("click", () => {
      $("signals-panel").classList.add("hidden");
      activeBotId = null;
    });
    $("btn-generate-signal").addEventListener("click", generateSignal);

    // Modal señal
    $("btn-signal-close").addEventListener("click", () => $("modal-signal").classList.add("hidden"));
    $("modal-signal").querySelector(".modal__backdrop").addEventListener("click", () =>
      $("modal-signal").classList.add("hidden"));

    if (window.lucide) lucide.createIcons();
  });
})();
