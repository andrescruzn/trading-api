# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/notifications/list_notifications_service.py
#
# PROPÓSITO:
# - Feed de la campana del header: últimos eventos de alerta del usuario
#   y cuántos son nuevos.
#
# NOTAS:
# - "Nuevo" = `ts` posterior a `users.notifications_seen_at`; si es NULL
#   (nunca abrió la campana) todos lo son.
# - Solo los eventos del propio usuario, también para un admin: la campana
#   es personal (la supervisión vive en /admin/alerts).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.common.contracts import ServiceResult
from app.common.utils import ensure_aware_utc
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository
from app.modules.users.domain.user_repository import UserRepository


@dataclass(frozen=True)
class Notification:
    """Un evento de alerta tal como lo muestra la campana."""

    event: AlertEvent
    is_new: bool


@dataclass(frozen=True)
class NotificationFeed:
    """Resultado del feed: eventos recientes + contador de no leídos."""

    items: list[Notification]
    unread_count: int
    seen_at: datetime | None


def _is_after(ts: datetime | None, seen_at: datetime | None) -> bool:
    if seen_at is None:
        return True
    ts_utc = ensure_aware_utc(ts)
    return ts_utc is not None and ts_utc > seen_at


class ListNotificationsService:
    """
    Lista las notificaciones del usuario autenticado.

    Reglas:
    - `limit` acotado a [1, MAX_LIMIT].
    - `unread_count` cuenta todos los eventos nuevos, no solo los listados.
    """

    MAX_LIMIT = 50

    def __init__(self, *, event_repo: AlertEventRepository, user_repo: UserRepository):
        self._event_repo = event_repo
        self._user_repo = user_repo

    def list(self, user_id: int, limit: int = 20) -> ServiceResult[NotificationFeed]:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        limit = max(1, min(int(limit), self.MAX_LIMIT))
        seen_at = ensure_aware_utc(user.notifications_seen_at)

        events = self._event_repo.list_by_user(user_id=user_id, limit=limit)
        unread_count = self._event_repo.count_by_user_after(user_id=user_id, after=seen_at)

        return ServiceResult.ok(
            data=NotificationFeed(
                items=[Notification(event=e, is_new=_is_after(e.ts, seen_at)) for e in events],
                unread_count=unread_count,
                seen_at=seen_at,
            )
        )
