# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/webhook_channel.py
#
# Canal de notificación via Webhook (HTTP POST a URL externa).
#
# SEGURIDAD (SSRF):
# - Antes de cada envío se resuelve el host y se exige que todas sus IPs
#   sean públicas (url_guard). Sin redirects: un 302 hacia una IP interna
#   no se sigue. La URL nunca se escribe en los logs (puede llevar tokens).
# ======================================================================

from __future__ import annotations

import logging

from app.common.security.url_guard import resolves_to_public_ips
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5


class WebhookChannel:
    """
    Canal Webhook — POST JSON al endpoint configurado en la regla.

    Payload enviado:
    {
        "event_id": 1,
        "title": "...",
        "severity": "info",
        "rule_name": "...",
        "message": "...",
        "payload": {...}
    }
    """

    def __init__(self, url: str):
        self._url = url

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        if not resolves_to_public_ips(self._url):
            logger.warning("WebhookChannel: URL bloqueada (no pública) en la regla %s", rule.id)
            return False

        try:
            import httpx

            body = {
                "event_id": event.id,
                "title": event.title,
                "severity": event.severity,
                "rule_name": rule.name,
                "message": event.message or "",
                "payload": event.payload,
            }
            resp = httpx.post(
                self._url,
                json=body,
                timeout=_TIMEOUT_SECONDS,
                follow_redirects=False,
            )
            if resp.status_code not in (200, 201, 202, 204):
                logger.warning(
                    "WebhookChannel HTTP %s en la regla %s", resp.status_code, rule.id
                )
                return False
            return True
        except Exception as exc:
            logger.error("WebhookChannel %s en la regla %s", type(exc).__name__, rule.id)
            return False
