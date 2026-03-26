// admin/telegram.js — Prueba de conexión Telegram

"use strict";

document.getElementById("btnTestTelegram").addEventListener("click", async () => {
  const btn = document.getElementById("btnTestTelegram");
  const resultEl = document.getElementById("testResult");
  btn.disabled = true;
  btn.textContent = "Enviando...";
  resultEl.style.display = "none";

  try {
    const res = await fetch("/api/alerts/test-telegram", {
      method: "POST",
      credentials: "include",
    });
    const json = await res.json();

    if (json.errorCode >= 400 || !json.data?.ok) {
      resultEl.innerHTML = `
        <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:0.875rem;">
          <strong style="color:#ef4444;">❌ Fallo al enviar</strong>
          <p style="font-size:0.8125rem;color:var(--text-secondary);margin-top:0.35rem;">${json.msg || "Error desconocido"}</p>
        </div>`;
    } else {
      resultEl.innerHTML = `
        <div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);border-radius:8px;padding:0.875rem;">
          <strong style="color:#22c55e;">✅ Mensaje enviado correctamente</strong>
          <p style="font-size:0.8125rem;color:var(--text-secondary);margin-top:0.35rem;">
            Revisa tu chat de Telegram para confirmar la recepción.
          </p>
        </div>`;
    }
    resultEl.style.display = "";
  } catch (e) {
    resultEl.innerHTML = `
      <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:0.875rem;">
        <strong style="color:#ef4444;">❌ Error de red</strong>
        <p style="font-size:0.8125rem;color:var(--text-secondary);margin-top:0.35rem;">${e.message}</p>
      </div>`;
    resultEl.style.display = "";
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="send" style="width:14px;height:14px;"></i> Enviar mensaje de prueba';
    if (typeof lucide !== "undefined") lucide.createIcons();
  }
});

if (typeof lucide !== "undefined") lucide.createIcons();
