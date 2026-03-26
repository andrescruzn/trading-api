# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/domain/alert_event_repository.py
#
# Contrato (Protocol) del repositorio de AlertEvents.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.modules.alerts.domain.alert_event_entity import AlertEvent


class AlertEventRepository(Protocol):

    def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        from_ts: datetime | None = None,
    ) -> list[AlertEvent]: ...

    def list_all(self, limit: int = 100) -> list[AlertEvent]: ...

    def create(self, event: AlertEvent) -> AlertEvent: ...

    def update(self, event: AlertEvent) -> AlertEvent: ...
