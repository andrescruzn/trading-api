# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository


class CreateAlertRuleService:

    def __init__(self, repo: AlertRuleRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(
        self,
        name: str,
        rule_type: str,
        rule_spec: dict[str, Any],
        channels: dict[str, Any],
        user_id: int | None = None,
        bot_id: int | None = None,
    ) -> ServiceResult[AlertRule]:
        if rule_type not in AlertRule.VALID_TYPES:
            return ServiceResult.fail(
                code="ALERT_RULE_INVALID_TYPE",
                http_status=422,
                meta={"rule_type": rule_type},
            )

        rule = AlertRule(
            id=0,
            name=name,
            rule_type=rule_type,
            rule_spec=rule_spec,
            channels=channels,
            is_active=True,
            user_id=user_id,
            bot_id=bot_id,
        )

        created = self._repo.create(rule)
        self._session.commit()
        return ServiceResult.ok(data=created)
