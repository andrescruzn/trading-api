# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/telegram_channel.py
#
# Canal de notificación via Telegram Bot API (HTTP POST directo).
# No requiere librería extra — usa httpx.
# ======================================================================

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.config.settings import Settings

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}


class TelegramChannel:
    """
    Canal Telegram — envía mensaje via Bot API.

    Requiere TELEGRAM_BOT_TOKEN y TELEGRAM_DEFAULT_CHAT_ID en settings.
    """

    def __init__(self, settings: "Settings", chat_id: str | None = None):
        self._token = settings.TELEGRAM_BOT_TOKEN
        self._chat_id = chat_id or settings.TELEGRAM_DEFAULT_CHAT_ID

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        if not self._token or not self._chat_id:
            logger.warning("TelegramChannel: bot token or chat_id not configured")
            return False

        try:
            import httpx

            emoji = _SEVERITY_EMOJI.get(event.severity, "🔔")
            text = (
                f"{emoji} *{event.title}*\n"
                f"Regla: {rule.name}\n"
                f"Severidad: {event.severity.upper()}\n"
            )
            if event.message:
                text += f"\n{event.message}"

            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            resp = httpx.post(
                url,
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(
                    "TelegramChannel HTTP %s: %s", resp.status_code, resp.text
                )
                return False
            return True
        except Exception as exc:
            logger.error("TelegramChannel exception: %s", exc)
            return False

    def send_raw(self, text: str) -> bool:
        """Envía texto libre — usado por el endpoint de prueba."""
        if not self._token or not self._chat_id:
            return False
        try:
            import httpx

            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            resp = httpx.post(
                url,
                json={"chat_id": self._chat_id, "text": text},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("TelegramChannel.send_raw exception: %s", exc)
            return False
