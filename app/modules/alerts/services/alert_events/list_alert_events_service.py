# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from app.common.contracts import ServiceResult
from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository


class ListAlertEventsService:

    def __init__(self, repo: AlertEventRepository):
        self._repo = repo

    def list(
        self,
        user_id: int | None = None,
        is_admin: bool = False,
        limit: int = 50,
        from_ts: datetime | None = None,
    ) -> ServiceResult[list[AlertEvent]]:
        if is_admin:
            events = self._repo.list_all(limit=limit)
        elif user_id is not None:
            events = self._repo.list_by_user(user_id=user_id, limit=limit, from_ts=from_ts)
        else:
            events = []
        return ServiceResult.ok(data=events)
