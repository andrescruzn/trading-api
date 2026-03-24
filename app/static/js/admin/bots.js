// ======================================================================
// static/js/admin/bots.js
//
// Vista admin: todos los bots del sistema con filtros de estado y modo.
// ======================================================================

(function () {
  "use strict";

  let allBots = [];

  const $ = id => document.getElementById(id);

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

  function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
  }

  // -----------------------------------------------------------------------
  // Cargar todos los bots
  // -----------------------------------------------------------------------
  async function loadBots() {
    $("table-loading").classList.remove("hidden");
    $("table-wrapper").classList.add("hidden");
    $("empty-state").classList.add("hidden");

    const res  = await fetch("/api/bots");
    const json = await res.json();

    $("table-loading").classList.add("hidden");
    allBots = json.data?.items || json.data || [];

    applyFilters();
  }

  function applyFilters() {
    const statusFilter = $("filter-status").value;
    const modeFilter   = $("filter-mode").value;

    const filtered = allBots.filter(b => {
      if (statusFilter && b.status !== statusFilter) return false;
      if (modeFilter   && b.mode   !== modeFilter)   return false;
      return true;
    });

    $("bots-count").textContent = `${filtered.length} de ${allBots.length} bots`;

    if (!filtered.length) {
      $("empty-state").classList.remove("hidden");
      $("table-wrapper").classList.add("hidden");
      return;
    }

    renderTable(filtered);
    $("table-wrapper").classList.remove("hidden");
    $("empty-state").classList.add("hidden");
  }

  function renderTable(bots) {
    const tbody = $("bots-tbody");
    tbody.innerHTML = "";

    bots.forEach(b => {
      const riskPct = b.risk_params?.risk_pct != null
        ? (parseFloat(b.risk_params.risk_pct) * 100).toFixed(1) + "%"
        : "—";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${b.id}</td>
        <td>${statusBadge(b.status)}</td>
        <td>${modeBadge(b.mode)}</td>
        <td>${b.account_id ?? "—"}</td>
        <td>${b.symbol_id}</td>
        <td>${b.timeframe_id}</td>
        <td>${b.strategy_id}</td>
        <td>${riskPct}</td>
        <td style="font-size:0.75rem;">${fmtDate(b.started_at)}</td>
        <td style="font-size:0.75rem;">${fmtDate(b.created_at)}</td>
        <td>
          <div style="display:flex;gap:0.3rem;">
            ${b.status === "stopped" ? `
            <button class="btn btn--primary btn-start" data-id="${b.id}"
              style="padding:0.2rem 0.55rem;font-size:0.7rem;width:auto;">▶ Start</button>` : ""}
            ${b.status === "running" ? `
            <button class="btn btn--secondary btn-pause" data-id="${b.id}"
              style="padding:0.2rem 0.55rem;font-size:0.7rem;width:auto;">⏸ Pause</button>` : ""}
            ${b.status !== "stopped" ? `
            <button class="btn btn--secondary btn-stop" data-id="${b.id}"
              style="padding:0.2rem 0.55rem;font-size:0.7rem;width:auto;color:#ef4444;">⏹ Stop</button>` : ""}
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".btn-start").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "start")));
    tbody.querySelectorAll(".btn-pause").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "pause")));
    tbody.querySelectorAll(".btn-stop").forEach(btn =>
      btn.addEventListener("click", () => changeStatus(+btn.dataset.id, "stop")));
  }

  async function changeStatus(botId, action) {
    const res  = await fetch(`/api/bots/${botId}/${action}`, { method: "POST" });
    const json = await res.json();

    if (!res.ok) {
      alert(json.msg || "Error al cambiar el estado.");
      return;
    }
    await loadBots();
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    loadBots();

    $("btn-refresh").addEventListener("click", loadBots);
    $("filter-status").addEventListener("change", applyFilters);
    $("filter-mode").addEventListener("change", applyFilters);

    if (window.lucide) lucide.createIcons();
  });
})();
