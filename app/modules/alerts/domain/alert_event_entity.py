# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/domain/alert_event_entity.py
#
# Entidad de dominio: AlertEvent.
# Evento disparado al activarse una AlertRule.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class AlertEvent:
    """
    Entidad de dominio: AlertEvent.

    Severidades:
    - info     : informativo (señal generada, orden ejecutada)
    - warning  : atención requerida (P&L negativo)
    - critical : acción urgente (drawdown excesivo, error en bot)

    Estados de entrega:
    - pending : creado, aún no despachado a los canales
    - sent    : entregado exitosamente a todos los canales activos
    - failed  : falló la entrega en al menos un canal
    """

    VALID_SEVERITIES = ("info", "warning", "critical")
    VALID_DELIVERIES = ("pending", "sent", "failed")

    def __init__(
        self,
        id: int,
        title: str,
        severity: str,
        payload: dict[str, Any],
        delivery_status: str = "pending",
        message: str | None = None,
        alert_rule_id: int | None = None,
        user_id: int | None = None,
        bot_id: int | None = None,
        ts: datetime | None = None,
    ):
        self.id = id
        self.title = title
        self.severity = severity
        self.payload = payload
        self.delivery_status = delivery_status
        self.message = message
        self.alert_rule_id = alert_rule_id
        self.user_id = user_id
        self.bot_id = bot_id
        self.ts = ts

    def mark_sent(self) -> None:
        self.delivery_status = "sent"

    def mark_failed(self) -> None:
        self.delivery_status = "failed"
