// ======================================================================
// static/js/orders/index.js
//
// Panel de órdenes del usuario:
// - Selector de bot
// - Tab Órdenes: tabla con historial de órdenes del bot
// - Tab Posiciones: grid de posiciones abiertas (qty, avg_price, P&L)
// - Tab Ejecuciones: tabla de fills (price, qty, fee, notional)
// - Modal Nueva Orden: crear order para el bot seleccionado
// - Modal Fills de Orden: ver fills de una orden específica
// ======================================================================

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Estado local
  // -----------------------------------------------------------------------
  let selectedBotId  = null;
  let activeTab      = "orders";   // "orders" | "positions" | "fills"
  let submitting     = false;

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

  function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
  }

  function fmtPrice(val, decimals = 4) {
    if (val == null) return "—";
    const n = parseFloat(val);
    if (isNaN(n)) return "—";
    return n.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: decimals,
    });
  }

  // Badge de lado (buy/sell)
  function sideBadge(side) {
    const cls = side === "buy" ? "badge--buy" : "badge--sell";
    return `<span class="badge ${cls}">${side.toUpperCase()}</span>`;
  }

  // Badge de estado de la orden
  function statusBadge(status) {
    const cls = `badge--${status.replace("_", "-")}`;
    return `<span class="badge ${cls}">${status}</span>`;
  }

  // -----------------------------------------------------------------------
  // Cargar bots en el selector
  // -----------------------------------------------------------------------
  async function loadBots() {
    const res  = await fetch("/api/bots");
    const json = await res.json();
    const bots = json.data?.items || json.data || [];

    const sel = $("select-bot");
    sel.innerHTML = `<option value="">— Selecciona un bot —</option>`;
    bots.forEach(b => {
      const opt = document.createElement("option");
      opt.value       = b.id;
      opt.textContent = `Bot #${b.id} · ${b.mode.toUpperCase()} · ${b.status}`;
      sel.appendChild(opt);
    });

    // También poblar el select del modal de nueva orden
    const selModal = $("o-bot");
    selModal.innerHTML = `<option value="">— Selecciona un bot —</option>`;
    bots.forEach(b => {
      const opt = document.createElement("option");
      opt.value       = b.id;
      opt.textContent = `Bot #${b.id} · ${b.mode.toUpperCase()} · ${b.status}`;
      selModal.appendChild(opt);
    });
  }

  // -----------------------------------------------------------------------
  // Cambio de bot seleccionado
  // -----------------------------------------------------------------------
  function onBotChange() {
    const val = $("select-bot").value;

    if (!val) {
      selectedBotId = null;
      $("tabs-wrapper").style.display = "none";
      clearAllTabs();
      return;
    }

    selectedBotId = +val;
    $("tabs-wrapper").style.display = "";
    // También preseleccionar en el modal
    $("o-bot").value = val;

    loadActiveTab();
  }

  function clearAllTabs() {
    // Órdenes
    $("orders-tbody").innerHTML = "";
    $("orders-table-wrapper").classList.add("hidden");
    $("orders-empty").classList.add("hidden");
    // Posiciones
    $("positions-grid").innerHTML = "";
    $("positions-empty").classList.add("hidden");
    // Fills
    $("fills-tbody").innerHTML = "";
    $("fills-table-wrapper").classList.add("hidden");
    $("fills-empty").classList.add("hidden");
  }

  // -----------------------------------------------------------------------
  // Tab switching
  // -----------------------------------------------------------------------
  function switchTab(tabName) {
    activeTab = tabName;

    // Actualizar clases de botones
    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    // Mostrar/ocultar paneles
    $("tab-orders").classList.toggle("hidden",    tabName !== "orders");
    $("tab-positions").classList.toggle("hidden", tabName !== "positions");
    $("tab-fills").classList.toggle("hidden",     tabName !== "fills");

    if (selectedBotId) loadActiveTab();
  }

  function loadActiveTab() {
    if (!selectedBotId) return;
    if (activeTab === "orders")    loadOrders();
    if (activeTab === "positions") loadPositions();
    if (activeTab === "fills")     loadFills();
  }

  // -----------------------------------------------------------------------
  // Tab: Órdenes
  // -----------------------------------------------------------------------
  async function loadOrders() {
    $("orders-loading").classList.remove("hidden");
    $("orders-table-wrapper").classList.add("hidden");
    $("orders-empty").classList.add("hidden");

    const res  = await fetch(`/api/orders?bot_id=${selectedBotId}`);
    const json = await res.json();

    $("orders-loading").classList.add("hidden");

    const orders = json.data?.items || json.data || [];

    if (!orders.length) {
      $("orders-empty").classList.remove("hidden");
      return;
    }

    renderOrdersTable(orders);
    $("orders-table-wrapper").classList.remove("hidden");
  }

  function renderOrdersTable(orders) {
    const tbody = $("orders-tbody");
    tbody.innerHTML = "";

    orders.forEach(o => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family:monospace;font-size:0.8rem;">${o.id}</td>
        <td>${sideBadge(o.side)}</td>
        <td style="font-size:0.8rem;font-family:monospace;">${o.type}</td>
        <td>${statusBadge(o.status)}</td>
        <td style="font-family:monospace;">${fmtPrice(o.qty, 8)}</td>
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

    // Event delegation — abrir modal de fills
    tbody.querySelectorAll(".btn-view-fills").forEach(btn =>
      btn.addEventListener("click", () => openFillsModal(+btn.dataset.orderId)));
  }

  // -----------------------------------------------------------------------
  // Tab: Posiciones
  // -----------------------------------------------------------------------
  async function loadPositions() {
    $("positions-loading").classList.remove("hidden");
    $("positions-grid").innerHTML = "";
    $("positions-empty").classList.add("hidden");

    const res  = await fetch(`/api/positions?bot_id=${selectedBotId}`);
    const json = await res.json();

    $("positions-loading").classList.add("hidden");

    const positions = json.data?.items || json.data || [];

    if (!positions.length) {
      $("positions-empty").classList.remove("hidden");
      return;
    }

    renderPositionsGrid(positions);
  }

  function renderPositionsGrid(positions) {
    const grid = $("positions-grid");
    grid.innerHTML = "";

    positions.forEach(p => {
      const pnl    = parseFloat(p.realized_pnl || 0);
      const pnlCls = pnl > 0 ? "pnl--positive" : pnl < 0 ? "pnl--negative" : "pnl--zero";
      const pnlTxt = (pnl >= 0 ? "+" : "") + fmtPrice(pnl);

      const card = document.createElement("div");
      card.className = "position-card";
      card.innerHTML = `
        <div class="position-card__symbol">Símbolo ID #${p.symbol_id}</div>
        <div class="position-card__qty">${fmtPrice(p.qty, 8)}</div>
        <div class="position-card__avg">
          Precio promedio: <strong>${fmtPrice(p.avg_price)}</strong>
        </div>
        <div class="position-card__pnl ${pnlCls}">
          P&amp;L Realizado: ${pnlTxt}
        </div>
        <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.4rem;">
          Actualizado: ${fmtDate(p.updated_at)}
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // -----------------------------------------------------------------------
  // Tab: Ejecuciones (fills del bot completo)
  // -----------------------------------------------------------------------
  async function loadFills() {
    $("fills-loading").classList.remove("hidden");
    $("fills-table-wrapper").classList.add("hidden");
    $("fills-empty").classList.add("hidden");

    const res  = await fetch(`/api/fills?bot_id=${selectedBotId}`);
    const json = await res.json();

    $("fills-loading").classList.add("hidden");

    const fills = json.data?.items || json.data || [];

    if (!fills.length) {
      $("fills-empty").classList.remove("hidden");
      return;
    }

    renderFillsTable(fills, $("fills-tbody"));
    $("fills-table-wrapper").classList.remove("hidden");
  }

  function renderFillsTable(fills, tbody) {
    tbody.innerHTML = "";

    fills.forEach(f => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family:monospace;font-size:0.8rem;">${f.id}</td>
        <td style="font-family:monospace;font-size:0.8rem;">#${f.order_id}</td>
        <td style="font-family:monospace;">${fmtPrice(f.qty, 8)}</td>
        <td style="font-family:monospace;">${fmtPrice(f.price)}</td>
        <td style="font-family:monospace;">${fmtPrice(f.notional_value)}</td>
        <td style="font-family:monospace;">
          ${fmtPrice(f.fee)}
          ${f.fee_asset ? `<span style="color:var(--text-muted);font-size:0.7rem;">${f.fee_asset}</span>` : ""}
        </td>
        <td style="font-size:0.75rem;">${fmtDate(f.ts)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // -----------------------------------------------------------------------
  // Modal: Fills de una orden específica
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
      $("fills-modal-content").innerHTML = `
        <p class="text-muted text-center">Esta orden no tiene ejecuciones todavía.</p>`;
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

    renderFillsTable(fills, $("fills-modal-tbody"));
  }

  // -----------------------------------------------------------------------
  // Modal: Nueva Orden — visibilidad dinámica de campos
  // -----------------------------------------------------------------------
  function updatePriceFields() {
    const type = $("o-type").value;
    const fieldPrice     = $("field-price");
    const fieldStopPrice = $("field-stop-price");

    // limit: solo precio límite
    // stop: solo stop price
    // stop_limit: ambos
    // market: ninguno
    const showPrice     = type === "limit"      || type === "stop_limit";
    const showStopPrice = type === "stop"       || type === "stop_limit";

    fieldPrice.style.display     = showPrice     ? "" : "none";
    fieldStopPrice.style.display = showStopPrice ? "" : "none";

    // Si no se muestran los campos, borrar valores para evitar enviarlos accidentalmente
    if (!showPrice)     $("o-price").value      = "";
    if (!showStopPrice) $("o-stop-price").value = "";
  }

  // -----------------------------------------------------------------------
  // Modal: Crear orden — submit
  // -----------------------------------------------------------------------
  async function submitCreateOrder(e) {
    e.preventDefault();
    if (submitting) return;

    const errEl = $("order-form-error");
    errEl.classList.add("hidden");

    const botId    = +$("o-bot").value;
    const side     = $("o-side").value;
    const type     = $("o-type").value;
    const qty      = parseFloat($("o-qty").value);
    const price    = $("o-price").value    ? parseFloat($("o-price").value)      : null;
    const stopPr   = $("o-stop-price").value ? parseFloat($("o-stop-price").value) : null;

    if (!botId) {
      errEl.textContent = "Selecciona un bot.";
      errEl.classList.remove("hidden");
      return;
    }

    submitting = true;
    const btn = $("btn-order-submit");
    btn.disabled    = true;
    btn.textContent = "Enviando...";

    const body = { bot_id: botId, side, type, qty };
    if (price    != null) body.price      = price;
    if (stopPr   != null) body.stop_price = stopPr;

    const res  = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await res.json();

    btn.disabled    = false;
    btn.textContent = "Ejecutar Orden";
    submitting      = false;

    if (!res.ok) {
      errEl.textContent = json.msg || "Error al ejecutar la orden.";
      errEl.classList.remove("hidden");
      return;
    }

    // Cerrar modal y recargar
    $("modal-order").classList.add("hidden");
    showAlert("Orden ejecutada correctamente.", "success");

    // Si el bot seleccionado en el modal coincide con el del selector principal,
    // refrescar los datos
    if (selectedBotId && selectedBotId === botId) {
      loadActiveTab();
    } else if (botId) {
      // Si no había bot seleccionado, seleccionarlo ahora
      $("select-bot").value = botId;
      onBotChange();
    }
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", async () => {
    // Cargar bots en ambos selectores
    await loadBots();

    // Selector de bot principal
    $("select-bot").addEventListener("change", onBotChange);

    // Tabs
    document.querySelectorAll(".tab-btn").forEach(btn =>
      btn.addEventListener("click", () => switchTab(btn.dataset.tab)));

    // Botón nueva orden → abre modal
    $("btn-new-order").addEventListener("click", () => {
      $("form-create-order").reset();
      updatePriceFields();   // market → sin campos de precio
      $("order-form-error").classList.add("hidden");
      $("modal-order").classList.remove("hidden");
    });

    // Cerrar modal de nueva orden
    $("btn-order-cancel").addEventListener("click",
      () => $("modal-order").classList.add("hidden"));
    $("modal-order").querySelector(".modal__backdrop").addEventListener("click",
      () => $("modal-order").classList.add("hidden"));

    // Campo tipo → actualizar visibilidad de precio/stop
    $("o-type").addEventListener("change", updatePriceFields);

    // Submit de nueva orden
    $("form-create-order").addEventListener("submit", submitCreateOrder);

    // Cerrar modal de fills
    $("btn-fills-close").addEventListener("click",
      () => $("modal-fills").classList.add("hidden"));
    $("modal-fills").querySelector(".modal__backdrop").addEventListener("click",
      () => $("modal-fills").classList.add("hidden"));

    // Inicializar Lucide icons
    if (window.lucide) lucide.createIcons();
  });
})();
