/* ======================================================================
   profile.js — Change password logic
   - PATCH /users/me/password
   - Al cambiar con éxito: el server borra la cookie → redirect a /login
   ====================================================================== */

"use strict";

// ── Show/hide password ───────────────────────────────────────────────

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const showing = input.type === "text";
  input.type = showing ? "password" : "text";
  btn.textContent = showing ? "Ver" : "Ocultar";
  btn.setAttribute("aria-label", showing ? "Mostrar contraseña" : "Ocultar contraseña");
}

// Toggle password: aplica a todos los botones con data-target
document.querySelectorAll(".toggle-password").forEach(function (btn) {
  btn.addEventListener("click", function () {
    togglePassword(this.dataset.target, this);
  });
});

// ── Alerts ───────────────────────────────────────────────────────────

function showAlert(message, type) {
  const el = document.getElementById("profile-alert");
  el.textContent = message;
  el.className = "alert alert--" + type + " show";
}

function hideAlert() {
  document.getElementById("profile-alert").className = "alert";
}

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

// Limpiar borde rojo al escribir en el campo
document.querySelectorAll("#current-password, #new-password, #confirm-password").forEach(function (input) {
  input.addEventListener("input", function () {
    this.classList.remove("input--error");
  });
});

// ── Loading ───────────────────────────────────────────────────────────

function setLoading(loading) {
  const btn = document.getElementById("btn-change-submit");
  btn.disabled = loading;
  btn.setAttribute("aria-busy", loading ? "true" : "false");
  if (loading) {
    btn._originalText = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span>';
  } else {
    btn.textContent = btn._originalText || "Guardar contraseña";
  }
}

// ── Form submit ──────────────────────────────────────────────────────

document.getElementById("form-change-password").addEventListener("submit", async function (e) {
  e.preventDefault();
  hideAlert();
  clearFieldErrors();

  const currentPassword = document.getElementById("current-password").value;
  const newPassword     = document.getElementById("new-password").value;
  const confirmPassword = document.getElementById("confirm-password").value;

  // Validación campo por campo con borde rojo
  if (!currentPassword) {
    setFieldError("current-password");
    showAlert("Ingresa tu contraseña actual.", "error");
    return;
  }

  if (!newPassword) {
    setFieldError("new-password");
    showAlert("Ingresa la nueva contraseña.", "error");
    return;
  }

  if (newPassword.length < 8) {
    setFieldError("new-password");
    showAlert("La nueva contraseña debe tener al menos 8 caracteres.", "error");
    return;
  }

  if (!confirmPassword) {
    setFieldError("confirm-password");
    showAlert("Confirma la nueva contraseña.", "error");
    return;
  }

  if (newPassword !== confirmPassword) {
    setFieldError("new-password");
    setFieldError("confirm-password");
    showAlert("La nueva contraseña y su confirmación no coinciden.", "error");
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/users/me/password", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password:     newPassword,
      }),
    });

    const json = await res.json();

    if (!res.ok || json.errorCode >= 400) {
      const fieldErrors = {
        "INVALID_CREDENTIALS":      "current-password",
        "PASSWORD_SAME_AS_CURRENT": "new-password",
        "PASSWORD_TOO_WEAK":        "new-password",
      };
      const msgs = {
        "INVALID_CREDENTIALS":      "La contraseña actual es incorrecta. Verifica e intenta de nuevo.",
        "PASSWORD_SAME_AS_CURRENT": "La nueva contraseña no puede ser igual a la contraseña actual.",
        "PASSWORD_TOO_WEAK":        "La contraseña no cumple los requisitos: mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula y 1 número.",
      };
      const field = fieldErrors[json.msg];
      if (field) setFieldError(field);
      showAlert(msgs[json.msg] || "Error inesperado. Intenta de nuevo.", "error");
      return;
    }

    // Éxito: el server ya borró la cookie → redirect directo (sin loop)
    showAlert("Contraseña cambiada. Redirigiendo...", "success");
    setTimeout(function () { window.location.href = "/login"; }, 1500);

  } catch (_) {
    showAlert("Error de conexión. Intenta de nuevo.", "error");
  } finally {
    setLoading(false);
  }
});
