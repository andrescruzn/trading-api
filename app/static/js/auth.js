/* ======================================================================
   auth.js — Login page logic
   Flujos:
   1. Password: email + password → POST /users/login → /dashboard
   2. OTP:      email → POST /users/login → OTP screen
               → POST /users/login/otp/verify → /dashboard

   NOTA: No se usan onclick inline (bloqueado por CSP script-src 'self').
         Todos los handlers se registran con addEventListener.
   ====================================================================== */

"use strict";

// ── Helpers ──────────────────────────────────────────────────────────

function showAlert(elId, message, type) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.textContent = message;
  el.className = "alert alert--" + type + " show";
}

function hideAlert(elId) {
  const el = document.getElementById(elId);
  if (el) el.className = "alert";
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.setAttribute("aria-busy", loading ? "true" : "false");
  if (loading) {
    btn._originalText = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span>';
  } else {
    btn.textContent = btn._originalText || btn.textContent;
  }
}

// ── Show/hide password ───────────────────────────────────────────────

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const showing = input.type === "text";
  input.type = showing ? "password" : "text";
  btn.textContent = showing ? "Ver" : "Ocultar";
  btn.setAttribute("aria-label", showing ? "Mostrar contraseña" : "Ocultar contraseña");
}

// ── Tab switching ────────────────────────────────────────────────────

function switchTab(tab) {
  const isPassword = tab === "password";
  document.getElementById("tab-password").classList.toggle("active", isPassword);
  document.getElementById("tab-otp").classList.toggle("active", !isPassword);
  document.getElementById("tab-password").setAttribute("aria-selected", isPassword ? "true" : "false");
  document.getElementById("tab-otp").setAttribute("aria-selected", isPassword ? "false" : "true");
  document.getElementById("panel-password").classList.toggle("hidden", !isPassword);
  document.getElementById("panel-otp-request").classList.toggle("hidden", isPassword);
  hideAlert("login-alert");
}

// ── Back to login from OTP screen ───────────────────────────────────

function backToLogin() {
  document.getElementById("step-login").classList.remove("hidden");
  document.getElementById("step-otp").classList.add("hidden");
  hideAlert("login-alert");
  hideAlert("otp-alert");
}

// ── Registrar handlers vía addEventListener (no onclick inline) ──────

document.getElementById("tab-password").addEventListener("click", function () {
  switchTab("password");
});

document.getElementById("tab-otp").addEventListener("click", function () {
  switchTab("otp");
});

document.getElementById("btn-back-to-login").addEventListener("click", backToLogin);

// Toggle password: aplica a todos los botones con data-target
document.querySelectorAll(".toggle-password").forEach(function (btn) {
  btn.addEventListener("click", function () {
    togglePassword(this.dataset.target, this);
  });
});

// ── Field error highlight ────────────────────────────────────────────

function setFieldError(inputId) {
  const el = document.getElementById(inputId);
  if (el) el.classList.add("input--error");
}

function clearFieldErrors() {
  document.querySelectorAll(".input--error").forEach(function (el) {
    el.classList.remove("input--error");
  });
}

// Limpiar borde rojo al escribir
["pw-email", "pw-password", "otp-email", "otp-code"].forEach(function (id) {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", function () { this.classList.remove("input--error"); });
});

// ── Form: Password login ─────────────────────────────────────────────

document.getElementById("form-password").addEventListener("submit", async function (e) {
  e.preventDefault();
  hideAlert("login-alert");
  clearFieldErrors();

  const email    = document.getElementById("pw-email").value.trim();
  const password = document.getElementById("pw-password").value;

  if (!email) {
    setFieldError("pw-email");
    showAlert("login-alert", "Ingresa tu correo electrónico.", "error");
    return;
  }

  if (!password) {
    setFieldError("pw-password");
    showAlert("login-alert", "Ingresa tu contraseña.", "error");
    return;
  }

  setLoading("btn-password-submit", true);

  try {
    const res = await fetch("/users/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });

    const json = await res.json();

    if (!res.ok || json.errorCode >= 400) {
      const msgs = {
        "INVALID_CREDENTIALS": "Correo o contraseña incorrectos.",
        "USER_NOT_ALLOWED":    "Tu cuenta no está activa.",
        "LOGIN_LOCKED":        "Cuenta bloqueada temporalmente por múltiples intentos fallidos.",
        "RATE_LIMIT_EXCEEDED": "Demasiados intentos. Espera un momento.",
      };
      if (json.msg === "INVALID_CREDENTIALS") {
        setFieldError("pw-email");
        setFieldError("pw-password");
      }
      showAlert("login-alert", msgs[json.msg] || "Error al iniciar sesión. Intenta de nuevo.", "error");
      return;
    }

    // Éxito → cookie seteada por el server
    window.location.href = "/dashboard";

  } catch (_) {
    showAlert("login-alert", "Error de conexión. Intenta de nuevo.", "error");
  } finally {
    setLoading("btn-password-submit", false);
  }
});

// ── Form: OTP request ───────────────────────────────────────────────

document.getElementById("form-otp-request").addEventListener("submit", async function (e) {
  e.preventDefault();
  hideAlert("login-alert");

  const email = document.getElementById("otp-email").value.trim();

  if (!email) {
    showAlert("login-alert", "Ingresa tu correo electrónico.", "error");
    return;
  }

  setLoading("btn-otp-request-submit", true);

  try {
    const res = await fetch("/users/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email }),
    });

    const json = await res.json();

    if (!res.ok || json.errorCode >= 400) {
      const msgs = {
        "INVALID_REQUEST":       "No encontramos una cuenta con ese correo.",
        "USER_NOT_ALLOWED":      "Tu cuenta no está activa.",
        "LOGIN_LOCKED":          "Cuenta bloqueada temporalmente por múltiples intentos fallidos.",
        "OTP_EMAIL_SEND_FAILED": "No pudimos enviar el correo. Intenta más tarde.",
        "RATE_LIMIT_EXCEEDED":   "Demasiados intentos. Espera un momento.",
      };
      showAlert("login-alert", msgs[json.msg] || "Error al enviar el código. Intenta de nuevo.", "error");
      return;
    }

    // otp_required → mostrar step 2
    const data = json.data || {};
    document.getElementById("otp-sent-email").textContent = data.email || email;
    document.getElementById("step-login").classList.add("hidden");
    document.getElementById("step-otp").classList.remove("hidden");
    document.getElementById("otp-code").focus();

    // Hint en development
    if (APP_ENV === "development" && data.otp_code) {
      document.getElementById("otp-dev-code").textContent = data.otp_code;
      document.getElementById("otp-dev-hint").style.display = "block";
    }

  } catch (_) {
    showAlert("login-alert", "Error de conexión. Intenta de nuevo.", "error");
  } finally {
    setLoading("btn-otp-request-submit", false);
  }
});

// ── Form: OTP verify ────────────────────────────────────────────────

document.getElementById("form-otp-verify").addEventListener("submit", async function (e) {
  e.preventDefault();
  hideAlert("otp-alert");

  const email   = document.getElementById("otp-sent-email").textContent.trim();
  const otpCode = document.getElementById("otp-code").value.trim();

  if (!otpCode || otpCode.length !== 6 || !/^\d{6}$/.test(otpCode)) {
    showAlert("otp-alert", "Ingresa el código de 6 dígitos.", "error");
    return;
  }

  setLoading("btn-otp-verify-submit", true);

  try {
    const res = await fetch("/users/login/otp/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, otp_code: otpCode }),
    });

    const json = await res.json();

    if (!res.ok || json.errorCode >= 400) {
      const msgs = {
        "OTP_INVALID":         "Código incorrecto. Verifica e intenta de nuevo.",
        "OTP_EXPIRED":         "El código ha expirado. Solicita uno nuevo.",
        "OTP_NOT_REQUESTED":   "No hay un código activo. Solicita uno nuevo.",
        "LOGIN_LOCKED":        "Cuenta bloqueada por múltiples intentos fallidos.",
        "RATE_LIMIT_EXCEEDED": "Demasiados intentos. Espera un momento.",
      };
      showAlert("otp-alert", msgs[json.msg] || "Código inválido. Intenta de nuevo.", "error");
      return;
    }

    // Éxito → cookie seteada por el server
    window.location.href = "/dashboard";

  } catch (_) {
    showAlert("otp-alert", "Error de conexión. Intenta de nuevo.", "error");
  } finally {
    setLoading("btn-otp-verify-submit", false);
  }
});

// ── OTP input: solo números ──────────────────────────────────────────

document.getElementById("otp-code").addEventListener("input", function () {
  this.value = this.value.replace(/\D/g, "").slice(0, 6);
});
