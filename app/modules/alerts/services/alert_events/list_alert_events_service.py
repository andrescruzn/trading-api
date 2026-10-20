# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/alert_events/list_alert_events_service.py
#
# Historial de eventos de alerta.
# - list():      los `limit` más recientes (lista simple).
# - list_page(): una página + el total ("Todas las alertas → Eventos" del
#                admin y el historial de /alerts).
# ======================================================================

from __future__ import annotations

from datetime import datetime

from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository


class ListAlertEventsService:
    """
    Reglas de negocio:
    - Admin: todos los eventos, o solo los del dueño `owner_filter` (filtro "Dueño").
    - Usuario: solo los suyos; `owner_filter` se ignora.
    - Sin usuario identificado: nada.
    - `from_ts` aplica a los dos roles. Orden: el más reciente primero.
    """

    def __init__(self, repo: AlertEventRepository):
        self._repo = repo

    def list(
        self,
        user_id: int | None = None,
        is_admin: bool = False,
        limit: int = 50,
        from_ts: datetime | None = None,
        owner_filter: int | None = None,
    ) -> ServiceResult[list[AlertEvent]]:
        allowed, scope = self._scope(user_id, is_admin, owner_filter)
        if not allowed:
            return ServiceResult.ok(data=[])
        return ServiceResult.ok(
            data=self._repo.search(user_id=scope, from_ts=from_ts, offset=0, limit=limit)
        )

    def list_page(
        self,
        page: PageRequest,
        user_id: int | None = None,
        is_admin: bool = False,
        from_ts: datetime | None = None,
        owner_filter: int | None = None,
    ) -> ServiceResult[Page[AlertEvent]]:
        allowed, scope = self._scope(user_id, is_admin, owner_filter)
        if not allowed:
            return ServiceResult.ok(data=Page.empty(page))
        total = self._repo.count(user_id=scope, from_ts=from_ts)
        items = (
            self._repo.search(
                user_id=scope, from_ts=from_ts, offset=page.offset, limit=page.limit
            )
            if total > page.offset
            else []
        )
        return ServiceResult.ok(
            data=Page(items=items, total=total, page=page.page, page_size=page.page_size)
        )

    @staticmethod
    def _scope(
        user_id: int | None, is_admin: bool, owner_filter: int | None
    ) -> tuple[bool, int | None]:
        """(puede ver algo, `user_id` por el que filtrar; None = todos los usuarios)."""
        if is_admin:
            return True, owner_filter
        if user_id is None:
            return False, None
        return True, int(user_id)
