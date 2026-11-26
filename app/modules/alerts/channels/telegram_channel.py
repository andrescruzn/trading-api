# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/telegram_channel.py
#
# Canal de notificación via Telegram Bot API (HTTP POST directo).
# No requiere librería extra — usa httpx.
#
# SEGURIDAD:
# - El token va en la URL de la Bot API: nunca se loguea la URL ni el
#   texto de la excepción de httpx (que la incluye), solo su tipo.
# - Mensajes con parse_mode HTML y todo texto variable escapado con
#   html.escape (un nombre de regla con `*` o `<` no rompe el mensaje).
# ======================================================================

from __future__ import annotations

import html
import logging
from typing import Any

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.notifications.domain import NotificationSettings

# telegram_api vive en el módulo notifications; se reexporta aquí porque
# los servicios de alerts lo importan desde este canal.
from app.modules.notifications.infrastructure.telegram_api import telegram_api

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}

__all__ = ["TelegramChannel", "telegram_api"]


class TelegramChannel:
    """
    Canal Telegram — envía mensaje via Bot API.

    Requiere Telegram activo en Administración → Notificaciones y un chat
    (el del usuario o el chat por defecto).
    """

    def __init__(self, settings: NotificationSettings, chat_id: str | int | None = None):
        self._token = settings.telegram_token
        self._chat_id = chat_id or settings.telegram_default_chat_id

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        emoji = _SEVERITY_EMOJI.get(event.severity, "🔔")
        text = (
            f"{emoji} <b>{html.escape(event.title)}</b>\n"
            f"Regla: {html.escape(rule.name)}\n"
            f"Severidad: {html.escape(event.severity.upper())}\n"
        )
        if event.message:
            text += f"\n{html.escape(event.message)}"

        return self.call("sendMessage", {"text": text, "parse_mode": "HTML"}) is not None

    def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Llama un método de la Bot API con el chat del canal.

        Returns:
            El `result` de Telegram, o None si falló (ya logueado sin el token).
        """
        if not self._token or not self._chat_id:
            logger.warning("TelegramChannel: Telegram inactivo o sin chat")
            return None
        return telegram_api(self._token, method, {"chat_id": self._chat_id, **payload})
