# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/channel_interface.py
#
# Protocolo (contrato) para los canales de notificación.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_rule_entity import AlertRule


class NotificationChannel(Protocol):
    """
    Contrato de canal de notificación.

    Implementaciones: EmailChannel, TelegramChannel, WebhookChannel, DesktopChannel.
    """

    def send(self, event: AlertEvent, rule: AlertRule) -> bool:
        """
        Envía la notificación.

        Retorna True si el envío fue exitoso, False en caso de fallo.
        NUNCA debe lanzar excepciones — captura internamente y retorna False.
        """
        ...
