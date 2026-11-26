# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/signal_email_messages.py
#
# PROPÓSITO:
# - Correos de las señales (rol notificación), equivalentes a los mensajes
#   de Telegram de telegram_messages.py:
#   - pending_signal_email: al dueño, señal por aprobar. Desde el correo
#     no se decide: el botón lleva al agente en Trading App.
#   - shared_signal_email: a quien sigue un agente compartido. Sin tamaño
#   de posición ni nombre del agente (no revela al dueño).
# - Devuelven (asunto, contexto) para NOTICE_TEMPLATE. Jinja escapa el
#   HTML, así que los valores van en claro.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.common.utils import utc_to_bogota
from app.modules.alerts.channels.telegram_messages import format_number

_PENDING_TITLE = {"buy": "Compra por aprobar", "sell": "Venta por aprobar"}
_SHARED_TITLE = {"buy": "Compra", "sell": "Venta"}


def _price(value: Decimal | None) -> str:
    return f"${format_number(value)}"


def pending_signal_email(
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
    url: str | None,
) -> tuple[str, dict[str, Any]]:
    title = f"{_PENDING_TITLE.get(action, 'Señal por aprobar')} · {symbol} · {timeframe}"
    details = [
        ("Entrada", _price(entry)),
        ("Stop loss", _price(stop_loss)),
        ("Take profit", _price(take_profit)),
        ("Riesgo/beneficio", f"{format_number(rr_ratio, 1)}:1"),
        ("Tamaño", f"{format_number(position_size, 6)} {base_asset}".strip()),
        ("Agente", f"{agent_name} · {'Live' if mode == 'live' else 'Paper'}"),
    ]
    if expires_at is not None:
        details.append(("Decide antes de", f"{utc_to_bogota(expires_at):%H:%M} (hora de Bogotá)"))
    return title, {
        "title": title,
        "message": f"Tu agente {agent_name} propone esta operación y espera tu decisión.",
        "details": details,
        "note": "Desde el correo no se puede aprobar ni descartar: decide en Trading App o en Telegram.",
        "url": url,
        "button_label": "Revisar en Trading App",
    }


def shared_signal_email(
    *,
    action: str,
    symbol: str,
    timeframe: str,
    strategy_name: str,
    entry: Decimal | None,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
    rr_ratio: Decimal | None,
) -> tuple[str, dict[str, Any]]:
    title = f"{_SHARED_TITLE.get(action, 'Señal')} · {symbol} · {timeframe}"
    return title, {
        "title": title,
        "message": (
            "Señal de un agente que sigues. Es informativa: no se abrió "
            "ninguna orden en tu cuenta."
        ),
        "details": [
            ("Entrada", _price(entry)),
            ("Stop loss", _price(stop_loss)),
            ("Take profit", _price(take_profit)),
            ("Riesgo/beneficio", f"{format_number(rr_ratio, 1)}:1"),
            ("Estrategia", strategy_name),
        ],
    }
