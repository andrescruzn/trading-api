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
from app.common.contracts import TransactionalRepository


class AlertEventRepository(TransactionalRepository, Protocol):

    def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        from_ts: datetime | None = None,
    ) -> list[AlertEvent]: ...

    def count_by_user_after(self, user_id: int, after: datetime | None = None) -> int:
        """Eventos del usuario con `ts` posterior a `after` (todos si es None)."""
        ...

    def search(
        self,
        user_id: int | None = None,
        from_ts: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AlertEvent]:
        """Eventos del usuario (todos si es None) desde `from_ts`, el más reciente
        primero (ts desc, id desc)."""
        ...

    def count(self, user_id: int | None = None, from_ts: datetime | None = None) -> int:
        """Total de eventos con los mismos filtros que `search` (paginación)."""
        ...

    def get_last_by_rule(self, rule_id: int) -> AlertEvent | None:
        """Último evento de la regla (antispam de las reglas periódicas)."""
        ...

    def create(self, event: AlertEvent) -> AlertEvent: ...

    def update(self, event: AlertEvent) -> AlertEvent: ...
