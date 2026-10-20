# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/alert_messages.py
#
# PROPÓSITO:
# - Título y mensaje de las alertas periódicas (precio, P&L, drawdown).
#   Rol notificación: lo importante en la primera línea, datos y sin hype.
#   Los canales escapan el texto (Telegram HTML) por su cuenta.
# - Números es-CO (format_number de telegram_messages).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.modules.alerts.channels.telegram_messages import format_number

_BELOW = ("lt", "lte")


def _amount(value: Decimal, currency: str) -> str:
    return f"{format_number(value)} {currency}".strip()


def _pct(value: Decimal) -> str:
    return f"{format_number(value, 2)} %"


def price_alert_text(
    *,
    symbol: str,
    quote_asset: str,
    operator: str,
    threshold: Decimal,
    price: Decimal,
) -> tuple[str, str]:
    side = "por debajo de" if operator in _BELOW else "por encima de"
    title = f"{symbol} {side} {_amount(threshold, quote_asset)}"
    message = (
        f"Último precio: {_amount(price, quote_asset)}. "
        f"Tu regla avisa cuando el precio está {side} {_amount(threshold, quote_asset)}."
    )
    return title, message


def pnl_alert_text(
    *,
    agent_name: str,
    period: str,
    pnl_pct: Decimal,
    pnl: Decimal,
    invested: Decimal,
    threshold: Decimal,
    quote_asset: str,
) -> tuple[str, str]:
    label = "PnL de hoy" if period == "daily" else "PnL total"
    title = f"{label} {_pct(pnl_pct)} · {agent_name}"
    message = (
        f"{label}: {_amount(pnl, quote_asset)} "
        f"({_pct(pnl_pct)} de {_amount(invested, quote_asset)} invertidos). "
        f"Umbral de la regla: {_pct(threshold)}."
    )
    return title, message


def drawdown_alert_text(
    *,
    agent_name: str,
    drawdown_pct: Decimal,
    drawdown: Decimal,
    invested: Decimal,
    threshold: Decimal,
    quote_asset: str,
) -> tuple[str, str]:
    title = f"Drawdown {_pct(drawdown_pct)} · {agent_name}"
    message = (
        f"Caída desde el mejor resultado: {_amount(drawdown, quote_asset)} "
        f"({_pct(drawdown_pct)} de {_amount(invested, quote_asset)} invertidos). "
        f"Umbral de la regla: {_pct(threshold)}. Revisa el agente en Trading App."
    )
    return title, message
