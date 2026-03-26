# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository


class UpdateAlertRuleService:

    def __init__(self, repo: AlertRuleRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        rule_id: int,
        name: str | None = None,
        rule_spec: dict[str, Any] | None = None,
        channels: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> ServiceResult[AlertRule]:
        rule = self._repo.get_by_id(rule_id)
        if rule is None:
            return ServiceResult.fail(code="ALERT_RULE_NOT_FOUND", http_status=404)

        if name is not None:
            rule.name = name
        if rule_spec is not None:
            rule.rule_spec = rule_spec
        if channels is not None:
            rule.channels = channels
        if is_active is not None:
            rule.is_active = is_active

        updated = self._repo.update(rule)
        self._session.commit()
        return ServiceResult.ok(data=updated)
