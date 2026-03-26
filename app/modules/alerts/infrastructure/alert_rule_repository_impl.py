# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/infrastructure/alert_rule_repository_impl.py
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.infrastructure.alert_rule_model import AlertRuleModel


def _to_entity(m: AlertRuleModel) -> AlertRule:
    return AlertRule(
        id=m.id,
        name=m.name,
        rule_type=m.rule_type,
        rule_spec=m.rule_spec or {},
        channels=m.channels or {},
        is_active=bool(m.is_active),
        user_id=m.user_id,
        bot_id=m.bot_id,
        created_at=m.created_at,
    )


class SqlAlchemyAlertRuleRepository:

    def __init__(self, session: Session):
        self._session = session

    def list_by_user(self, user_id: int) -> list[AlertRule]:
        rows = (
            self._session.query(AlertRuleModel)
            .filter(AlertRuleModel.user_id == user_id)
            .order_by(AlertRuleModel.created_at.desc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def list_all(self) -> list[AlertRule]:
        rows = (
            self._session.query(AlertRuleModel)
            .order_by(AlertRuleModel.created_at.desc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def list_active_by_type_and_bot(
        self, rule_type: str, bot_id: int | None = None
    ) -> list[AlertRule]:
        q = self._session.query(AlertRuleModel).filter(
            AlertRuleModel.rule_type == rule_type,
            AlertRuleModel.is_active == True,  # noqa: E712
        )
        if bot_id is not None:
            q = q.filter(AlertRuleModel.bot_id == bot_id)
        return [_to_entity(r) for r in q.all()]

    def get_by_id(self, rule_id: int) -> AlertRule | None:
        row = self._session.query(AlertRuleModel).filter(
            AlertRuleModel.id == rule_id
        ).first()
        return _to_entity(row) if row else None

    def create(self, rule: AlertRule) -> AlertRule:
        model = AlertRuleModel(
            user_id=rule.user_id,
            bot_id=rule.bot_id,
            name=rule.name,
            rule_type=rule.rule_type,
            rule_spec=rule.rule_spec,
            channels=rule.channels,
            is_active=rule.is_active,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, rule: AlertRule) -> AlertRule:
        model = self._session.query(AlertRuleModel).filter(
            AlertRuleModel.id == rule.id
        ).first()
        if model is None:
            raise ValueError(f"AlertRule {rule.id} not found")
        model.name = rule.name
        model.rule_spec = rule.rule_spec
        model.channels = rule.channels
        model.is_active = rule.is_active
        self._session.flush()
        return _to_entity(model)
