# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/bot_history.py
#
# PROPÓSITO:
# - Historial de un agente: quién lo creó, editó, arrancó, pausó o detuvo,
#   y cuándo el sistema lo cambió de estado. Se guarda en `audit_logs`.
#
# EVENTOS (`event_type`, ≤ 32 caracteres) y su `data`:
# - BOT_CREATED         {mode, execution_mode, risk_pct}
# - BOT_UPDATED         {changes: {campo: [antes, después]}}
# - BOT_STATUS_CHANGED  {from, to, reason?}  (reason solo si lo cambió el sistema)
#
# `user_id` = quién actuó; None = el sistema (p. ej. drawdown máximo).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

BOT_CREATED = "BOT_CREATED"
BOT_UPDATED = "BOT_UPDATED"
BOT_STATUS_CHANGED = "BOT_STATUS_CHANGED"

# Motivos de un cambio de estado que no pidió nadie desde la página del agente.
REASON_MAX_DRAWDOWN = "BOT_MAX_DRAWDOWN_REACHED"
REASON_OWNER_DISABLED = "OWNER_DISABLED"


@dataclass(frozen=True)
class BotHistoryEntry:
    """Un evento del historial de un agente."""
    id: int
    bot_id: int
    event_type: str
    ts: datetime
    data: dict[str, Any] = field(default_factory=dict)
    user_id: int | None = None
    user_name: str | None = None


def status_change_data(old: str, new: str, reason: str | None = None) -> dict[str, Any]:
    """`data` de BOT_STATUS_CHANGED."""
    data: dict[str, Any] = {"from": old, "to": new}
    if reason:
        data["reason"] = reason
    return data
