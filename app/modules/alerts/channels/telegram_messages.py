# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/telegram_messages.py
#
# PROPÓSITO:
# - Textos que el bot de Telegram envía a la persona (rol notificación:
#   directo, con datos, sin hype). Los servicios devuelven códigos; aquí
#   se convierten en texto, igual que error_messages.py en la API.
# - Formato de números es-CO: miles con punto, decimales con coma.
# ======================================================================

from __future__ import annotations

import html
from datetime import datetime
from decimal import Decimal

from app.common.utils import utc_to_bogota

# Respuesta corta al pulsar un botón (answerCallbackQuery, ≤ 200 caracteres)
# y línea que se agrega al mensaje original (editMessageText).
DECISION_MESSAGES: dict[str, str] = {
    "SIGNAL_EXECUTED":            "Aprobada: la orden se envió.",
    "SIGNAL_REJECTED":            "Rechazada: no se abrió ninguna orden.",
    "SIGNAL_ALREADY_DECIDED":     "Esta señal ya se decidió antes.",
    "SIGNAL_EXPIRED":             "La señal venció sin decisión; no se ejecutó.",
    "SIGNAL_NOT_FOUND":           "No encontramos esta señal en tu cuenta.",
    "SIGNAL_PRICE_MOVED":         "El precio se movió y la operación ya no cumple el riesgo/beneficio mínimo. No se ejecutó.",
    "SIGNAL_POSITION_ALREADY_OPEN": "El agente ya tiene una posición abierta. No se ejecutó.",
    "SIGNAL_NO_POSITION":         "El agente no tiene una posición que vender. No se ejecutó.",
    "TRADING_DISABLED":           "El envío de órdenes está detenido por el administrador. No se ejecutó.",
    "TRADING_LIVE_DISABLED":      "Las órdenes live están desactivadas. No se ejecutó.",
    "BOT_NOT_RUNNING":            "El agente no está activo. Inícialo y vuelve a intentarlo.",
    "BOT_MAX_DRAWDOWN_REACHED":   "El agente alcanzó su pérdida máxima y se detuvo. No se ejecutó.",
    "ORDER_NOTIONAL_TOO_HIGH":    "La orden supera el valor máximo por operación. No se ejecutó.",
    "CHAT_NOT_LINKED":            "Este chat no está vinculado. Conéctalo desde Trading App.",
}
DEFAULT_DECISION_MESSAGE = "No se pudo ejecutar la orden. Revísala en Trading App."

LINK_MESSAGES: dict[str, str] = {
    "TELEGRAM_LINKED": (
        "Listo: este chat quedó vinculado a tu cuenta de Trading App. "
        "Aquí te llegarán las señales por aprobar."
    ),
    "TELEGRAM_LINK_INVALID": (
        "El enlace venció o ya se usó. Genera uno nuevo en Trading App, "
        "en el menú de tu usuario → Conectar Telegram."
    ),
    "TELEGRAM_START_WITHOUT_CODE": (
        "Para recibir aquí tus señales, abre Trading App y elige "
        "Conectar Telegram en el menú de tu usuario."
    ),
}

BUTTON_APPROVE = "Aprobar"
BUTTON_REJECT = "Rechazar"
BUTTON_OPEN_APP = "Ver en Trading App"

_ACTION_LINE = {
    "buy": "🟢 Compra por aprobar",
    "sell": "🔴 Venta por aprobar",
}


def format_number(value: Decimal | float | None, decimals: int | None = None) -> str:
    """1234.5 → "1.234,50" (es-CO). Precios < 1 con más decimales."""
    if value is None:
        return "—"
    number = Decimal(str(value))
    if decimals is None:
        decimals = 2 if abs(number) >= 1 else 6
    text = f"{number:,.{decimals}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def pending_signal_text(
    *,
    action: str,
    symbol: str,
    timeframe: str,
    entry: Decimal | None,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
    rr_ratio: Decimal | None,
    position_size: Decimal | None,
    base_asset: str,
    agent_name: str,
    mode: str,
    expires_at: datetime | None,
) -> str:
    """Mensaje HTML de una señal pendiente (todo texto variable escapado)."""
    lines = [
        f"<b>{_ACTION_LINE.get(action, 'Señal por aprobar')} · "
        f"{html.escape(symbol)} · {html.escape(timeframe)}</b>",
        f"Entrada ${format_number(entry)} · SL ${format_number(stop_loss)} · "
        f"TP ${format_number(take_profit)}",
        f"R/R {format_number(rr_ratio, 1)}:1 · Tamaño {format_number(position_size, 6)} "
        f"{html.escape(base_asset)}",
        f"Agente {html.escape(agent_name)} · {'Live' if mode == 'live' else 'Paper'}",
    ]
    if expires_at is not None:
        local = utc_to_bogota(expires_at)
        lines.append(f"Decide antes de las {local:%H:%M} (hora de Bogotá).")
    return "\n".join(lines)


def decision_text(code: str) -> str:
    return DECISION_MESSAGES.get(code, DEFAULT_DECISION_MESSAGE)
