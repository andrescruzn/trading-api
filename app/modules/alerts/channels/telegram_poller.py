# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/telegram_poller.py
#
# PROPÓSITO:
# - En desarrollo Telegram no puede llamar a localhost: con
#   TELEGRAM_UPDATES_MODE=polling el scheduler pide los updates con
#   getUpdates en cada ciclo (solo el proceso líder).
#
# NOTAS:
# - El offset vive en memoria: tras reiniciar, Telegram reenvía lo no
#   confirmado (≤ 24 h). Es seguro: aprobar/rechazar es atómico y los
#   códigos de vinculación son de un solo uso.
# - getUpdates no funciona si hay un webhook registrado (deleteWebhook).
# ======================================================================

from __future__ import annotations

from typing import Any

from app.modules.alerts.channels.telegram_channel import telegram_api

_offset: int | None = None


def fetch_updates(token: str, limit: int = 50) -> list[dict[str, Any]]:
    """Updates nuevos desde el último llamado (y los confirma moviendo el offset)."""
    global _offset

    payload: dict[str, Any] = {
        "timeout": 0,
        "limit": limit,
        "allowed_updates": ["message", "callback_query"],
    }
    if _offset is not None:
        payload["offset"] = _offset

    result = telegram_api(token, "getUpdates", payload)
    updates = result.get("value") if isinstance(result, dict) else None
    if not isinstance(updates, list):
        return []

    valid = [u for u in updates if isinstance(u, dict) and isinstance(u.get("update_id"), int)]
    if valid:
        _offset = max(u["update_id"] for u in valid) + 1
    return valid
