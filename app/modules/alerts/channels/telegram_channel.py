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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.common.config.settings import Settings

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10

_SEVERITY_EMOJI = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}


class TelegramChannel:
    """
    Canal Telegram — envía mensaje via Bot API.

    Requiere TELEGRAM_BOT_TOKEN y un chat (el del usuario o
    TELEGRAM_DEFAULT_CHAT_ID).
    """

    def __init__(self, settings: "Settings", chat_id: str | int | None = None):
        self._token = settings.TELEGRAM_BOT_TOKEN
        self._chat_id = chat_id or settings.TELEGRAM_DEFAULT_CHAT_ID

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

    def send_raw(self, text: str) -> bool:
        """Envía texto libre — usado por el endpoint de prueba."""
        return self.call("sendMessage", {"text": text}) is not None

    def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Llama un método de la Bot API con el chat del canal.

        Returns:
            El `result` de Telegram, o None si falló (ya logueado sin el token).
        """
        if not self._token or not self._chat_id:
            logger.warning("TelegramChannel: bot token or chat_id not configured")
            return None
        return telegram_api(self._token, method, {"chat_id": self._chat_id, **payload})


def telegram_api(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    POST a https://api.telegram.org/bot<token>/<method>.

    Returns:
        El campo `result` si Telegram respondió ok, o None.
    """
    try:
        import httpx

        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
            timeout=_TIMEOUT_SECONDS,
        )
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code != 200 or not body.get("ok"):
            logger.warning(
                "Telegram %s HTTP %s: %s",
                method,
                resp.status_code,
                str(body.get("description", ""))[:200],
            )
            return None
        result = body.get("result")
        return result if isinstance(result, dict) else {"value": result}
    except Exception as exc:
        logger.error("Telegram %s %s", method, type(exc).__name__)
        return None
