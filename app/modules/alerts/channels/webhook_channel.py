# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/webhook_channel.py
#
# Canal de notificación via Webhook (HTTP POST a URL externa).
# ======================================================================

from __future__ import annotations

import logging

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule

logger = logging.getLogger(__name__)


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
            resp = httpx.post(self._url, json=body, timeout=10)
            if resp.status_code not in (200, 201, 202, 204):
                logger.warning(
                    "WebhookChannel HTTP %s for %s", resp.status_code, self._url
                )
                return False
            return True
        except Exception as exc:
            logger.error("WebhookChannel exception: %s", exc)
            return False
