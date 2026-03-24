// ======================================================================
// static/js/admin/orders.js
//
// Vista admin: todas las órdenes del sistema con filtros de lado,
// estado y tipo. Permite ver los fills de cada orden.
// ======================================================================

(function () {
  "use strict";

  let allOrders = [];

  const $ = id => document.getElementById(id);

  function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
  }

  function fmtPrice(val) {
    if (val == null) return "—";
    const n = parseFloat(val);
    return isNaN(n) ? "—" : n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 });
  }

  function sideBadge(side) {
    const cls = side === "buy" ? "badge--buy" : "badge--sell";
    return `<span class="badge ${cls}">${side.toUpperCase()}</span>`;
  }

  function statusBadge(status) {
    const cls = `badge--${status.replace("_", "-")}`;
    return `<span class="badge ${cls}">${status}</span>`;
  }

  // -----------------------------------------------------------------------
  // Cargar todas las órdenes (sin filtro → admin ve todo)
  // -----------------------------------------------------------------------
  async function loadOrders() {
    $("table-loading").classList.remove("hidden");
    $("table-wrapper").classList.add("hidden");
    $("empty-state").classList.add("hidden");

    const res  = await fetch("/api/orders");
    const json = await res.json();

    $("table-loading").classList.add("hidden");
    allOrders = json.data?.items || json.data || [];

    applyFilters();
  }

  function applyFilters() {
    const sideFilter   = $("filter-side").value;
    const statusFilter = $("filter-status").value;
    const typeFilter   = $("filter-type").value;

    const filtered = allOrders.filter(o => {
      if (sideFilter   && o.side   !== sideFilter)   return false;
      if (statusFilter && o.status !== statusFilter) return false;
      if (typeFilter   && o.type   !== typeFilter)   return false;
      return true;
    });

    $("orders-count").textContent = `${filtered.length} de ${allOrders.length} órdenes`;

    if (!filtered.length) {
      $("empty-state").classList.remove("hidden");
      $("table-wrapper").classList.add("hidden");
      return;
    }

    renderTable(filtered);
    $("table-wrapper").classList.remove("hidden");
    $("empty-state").classList.add("hidden");
  }

  function renderTable(orders) {
    const tbody = $("orders-tbody");
    tbody.innerHTML = "";

    orders.forEach(o => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family:monospace;font-size:0.8rem;">${o.id}</td>
        <td style="font-family:monospace;font-size:0.8rem;">#${o.bot_id}</td>
        <td>${sideBadge(o.side)}</td>
        <td style="font-size:0.8rem;font-family:monospace;">${o.type}</td>
        <td>${statusBadge(o.status)}</td>
        <td style="font-family:monospace;">${fmtPrice(o.qty)}</td>
        <td style="font-family:monospace;">${fmtPrice(o.price)}</td>
        <td style="font-family:monospace;">${fmtPrice(o.stop_price)}</td>
        <td style="font-size:0.75rem;color:var(--text-muted);">${o.signal_id ? `#${o.signal_id}` : "—"}</td>
        <td style="font-size:0.75rem;">${fmtDate(o.ts)}</td>
        <td>
          <button class="btn btn--secondary btn-view-fills"
            data-order-id="${o.id}"
            style="padding:0.2rem 0.55rem;font-size:0.7rem;width:auto;">
            Ver fills
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".btn-view-fills").forEach(btn =>
      btn.addEventListener("click", () => openFillsModal(+btn.dataset.orderId)));
  }

  // -----------------------------------------------------------------------
  // Modal: Fills de una orden
  // -----------------------------------------------------------------------
  async function openFillsModal(orderId) {
    $("fills-order-id").textContent = orderId;
    $("fills-modal-content").innerHTML = `
      <div class="text-center" style="padding:1rem;">
        <span class="spinner"></span>
        <p class="text-muted mt-1">Cargando ejecuciones...</p>
      </div>`;
    $("modal-fills").classList.remove("hidden");

    const res  = await fetch(`/api/fills?order_id=${orderId}`);
    const json = await res.json();
    const fills = json.data?.items || json.data || [];

    if (!fills.length) {
      $("fills-modal-content").innerHTML =
        `<p class="text-muted text-center">Esta orden no tiene ejecuciones todavía.</p>`;
      return;
    }

    $("fills-modal-content").innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th><th>Qty</th><th>Precio</th>
            <th>Nocional</th><th>Comisión</th><th>Timestamp</th>
          </tr>
        </thead>
        <tbody id="fills-modal-tbody"></tbody>
      </table>`;

    const tbody = $("fills-modal-tbody");
    fills.forEach(f => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family:monospace;font-size:0.8rem;">${f.id}</td>
        <td style="font-family:monospace;">${fmtPrice(f.qty)}</td>
        <td style="font-family:monospace;">${fmtPrice(f.price)}</td>
        <td style="font-family:monospace;">${fmtPrice(f.notional_value)}</td>
        <td style="font-family:monospace;">
          ${fmtPrice(f.fee)}
          ${f.fee_asset ? `<span style="color:var(--text-muted);font-size:0.7rem;"> ${f.fee_asset}</span>` : ""}
        </td>
        <td style="font-size:0.75rem;">${fmtDate(f.ts)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    loadOrders();

    $("btn-refresh").addEventListener("click", loadOrders);
    $("filter-side").addEventListener("change",   applyFilters);
    $("filter-status").addEventListener("change", applyFilters);
    $("filter-type").addEventListener("change",   applyFilters);

    $("btn-fills-close").addEventListener("click",
      () => $("modal-fills").classList.add("hidden"));
    $("modal-fills").querySelector(".modal__backdrop").addEventListener("click",
      () => $("modal-fills").classList.add("hidden"));

    if (window.lucide) lucide.createIcons();
  });
})();
