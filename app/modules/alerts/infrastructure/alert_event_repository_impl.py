# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_event_repository_impl.py
# ======================================================================

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.infrastructure.alert_event_model import AlertEventModel


def _to_entity(m: AlertEventModel) -> AlertEvent:
    return AlertEvent(
        id=m.id,
        title=m.title,
        severity=m.severity,
        payload=m.payload or {},
        delivery_status=m.delivery_status,
        message=m.message,
        alert_rule_id=m.alert_rule_id,
        user_id=m.user_id,
        bot_id=m.bot_id,
        ts=m.ts,
    )


class SqlAlchemyAlertEventRepository:

    def __init__(self, session: Session):
        self._session = session

    def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        from_ts: datetime | None = None,
    ) -> list[AlertEvent]:
        q = self._session.query(AlertEventModel).filter(
            AlertEventModel.user_id == user_id
        )
        if from_ts:
            q = q.filter(AlertEventModel.ts >= from_ts)
        rows = q.order_by(AlertEventModel.ts.desc()).limit(limit).all()
        return [_to_entity(r) for r in rows]

    def list_all(self, limit: int = 100) -> list[AlertEvent]:
        rows = (
            self._session.query(AlertEventModel)
            .order_by(AlertEventModel.ts.desc())
            .limit(limit)
            .all()
        )
        return [_to_entity(r) for r in rows]

    def create(self, event: AlertEvent) -> AlertEvent:
        model = AlertEventModel(
            alert_rule_id=event.alert_rule_id,
            user_id=event.user_id,
            bot_id=event.bot_id,
            severity=event.severity,
            title=event.title,
            message=event.message,
            payload=event.payload,
            delivery_status=event.delivery_status,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, event: AlertEvent) -> AlertEvent:
        model = self._session.query(AlertEventModel).filter(
            AlertEventModel.id == event.id
        ).first()
        if model is None:
            raise ValueError(f"AlertEvent {event.id} not found")
        model.delivery_status = event.delivery_status
        self._session.flush()
        return _to_entity(model)
