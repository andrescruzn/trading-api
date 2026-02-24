/* ======================================================================
   dashboard.js — Dashboard logic
   - Carga datos del usuario via GET /users/me
   - Maneja logout via POST /users/logout
   ====================================================================== */

"use strict";

// ── Load user data ───────────────────────────────────────────────────

async function loadMe() {
  try {
    const res = await fetch("/users/me", {
      method: "GET",
      credentials: "include",
    });

    if (res.status === 401 || res.status === 403) {
      window.location.href = "/login";
      return;
    }

    const json = await res.json();

    if (!res.ok || !json.data) {
      showError();
      return;
    }

    renderDashboard(json.data);

  } catch (_) {
    showError();
  }
}

function renderDashboard(user) {
  const name = user.full_name || user.email.split("@")[0];
  const isAdmin = user.role_label === "Administrador";

  // Greeting
  document.getElementById("dash-greeting").textContent = "Hola, " + name;
  document.getElementById("dash-email").textContent = user.email;

  // Nav badge
  const badge = document.getElementById("nav-role-badge");
  badge.className = "badge " + (isAdmin ? "badge--admin" : "badge--user");
  badge.textContent = user.role_label;

  // Info cards
  document.getElementById("info-email").textContent  = user.email;
  document.getElementById("info-role").textContent   = user.role_label;
  document.getElementById("info-status").textContent = capitalize(user.status);

  if (user.last_login_at) {
    const dt = new Date(user.last_login_at);
    document.getElementById("info-last-login").textContent = dt.toLocaleString("es-CO", {
      dateStyle: "medium", timeStyle: "short",
    });
  } else {
    document.getElementById("info-last-login").textContent = "Primera sesión";
  }

  // Show content
  document.getElementById("dashboard-loading").classList.add("hidden");
  document.getElementById("dashboard-content").classList.remove("hidden");
}

function showError() {
  document.getElementById("dashboard-loading").classList.add("hidden");
  document.getElementById("dashboard-error").classList.remove("hidden");
}

function capitalize(str) {
  if (!str) return "—";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Logout ───────────────────────────────────────────────────────────

async function logout() {
  try {
    await fetch("/users/logout", {
      method: "POST",
      credentials: "include",
    });
  } finally {
    window.location.href = "/login";
  }
}

// ── Init ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {
  loadMe();
  document.getElementById("btn-logout-nav").addEventListener("click", logout);
  document.getElementById("btn-logout-main").addEventListener("click", logout);
});
