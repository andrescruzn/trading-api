// sidebar.js — Hidratación del aside y topbar para todas las páginas de app
// Corre al final del body (DOM ya construido). No requiere DOMContentLoaded.
"use strict";

(async function initSidebar() {

  /* ── Marcar link activo ─────────────────────────────────────────────── */
  var path = window.location.pathname;
  document.querySelectorAll(".sidebar__link[data-path]").forEach(function (link) {
    if (link.dataset.path === path) {
      link.classList.add("active");
    }
  });

  /* ── Logout ─────────────────────────────────────────────────────────── */
  function doLogout() {
    fetch("/users/logout", { method: "POST", credentials: "include" })
      .finally(function () { window.location.href = "/login"; });
  }

  // btn-logout-main: botón de sidebar footer (visible en todas las páginas)
  var btnMain = document.getElementById("btn-logout-main");
  if (btnMain) btnMain.addEventListener("click", doLogout);

  // btn-logout-nav: elemento oculto — requerido por dashboard.js
  var btnNav = document.getElementById("btn-logout-nav");
  if (btnNav) btnNav.addEventListener("click", doLogout);

  /* ── Fetch usuario ──────────────────────────────────────────────────── */
  try {
    var res = await fetch("/users/me", { credentials: "include" });
    if (!res.ok) { window.location.href = "/login"; return; }

    var json = await res.json();
    var user  = json.data;
    var isAdmin    = user.role_label === "Administrador";
    var isInvestor = user.role_label === "Inversor";

    /* Email en sidebar footer */
    var emailEl = document.getElementById("sidebar-user-email");
    if (emailEl) emailEl.textContent = user.email || "—";

    /* Badge de rol en sidebar footer */
    var roleEl = document.getElementById("sidebar-user-role");
    if (roleEl) {
      roleEl.className  = "badge " + (isAdmin ? "badge--admin" : "badge--user");
      roleEl.textContent = user.role_label || "";
    }

    /* Nombre en topbar */
    var topbarUser = document.getElementById("topbar-user");
    if (topbarUser) {
      topbarUser.textContent = user.full_name || user.email.split("@")[0];
    }

    /* Badge de rol en topbar (nav-role-badge también lo usa dashboard.js) */
    var badge = document.getElementById("nav-role-badge");
    if (badge) {
      badge.className   = "badge " + (isAdmin ? "badge--admin" : "badge--user");
      badge.textContent = user.role_label || "";
    }

    /* Sección admin en sidebar */
    if (isAdmin) {
      var adminPanel = document.getElementById("admin-panel");
      if (adminPanel) adminPanel.classList.remove("hidden");
    }

    /* Sección investor en sidebar */
    if (isInvestor) {
      var investorPanel = document.getElementById("investor-panel");
      if (investorPanel) investorPanel.classList.remove("hidden");
    }

    /* Re-inicializar iconos Lucide tras cambios en DOM */
    if (window.lucide) lucide.createIcons();

  } catch (e) {
    window.location.href = "/login";
  }

  const buttonTopbar = document.querySelector(".topbar__button button");
  buttonTopbar.addEventListener("click", () => {
    const isOpen = document.documentElement.classList.contains("sidebar-open");

    if (isOpen) {
      document.documentElement.classList.remove("sidebar-open");
      unlockScroll();
    } else {
      document.documentElement.classList.add("sidebar-open");
      lockScroll();
    }
  })

  function getScrollbarWidth() {
    return window.innerWidth
        - document.documentElement.clientWidth;
  }

  function lockScroll() {
    const sb = getScrollbarWidth();

    const y = window.scrollY;
    document.body.dataset.scrollY = y;

    document.body.style.overflow  = 'hidden';
    document.body.style.position  = 'fixed';
    document.body.style.top       = `-${y}px`;
    document.body.style.width     = '100%';
    document.body.style.paddingRight = `${sb}px`;

    document.querySelectorAll('[data-lock-pad]')
      .forEach(el => {
        const cur = parseInt(getComputedStyle(el).paddingRight);
        el.style.paddingRight = `${cur + sb}px`;
      });
  }

  function unlockScroll() {
    const y = parseInt(document.body.dataset.scrollY || '0');

    document.body.style.overflow     = '';
    document.body.style.position     = '';
    document.body.style.top          = '';
    document.body.style.width        = '';
    document.body.style.paddingRight = '';

    document.querySelectorAll('[data-lock-pad]')
      .forEach(el => el.style.paddingRight = '');

    window.scrollTo(0, y);
  }
})();
