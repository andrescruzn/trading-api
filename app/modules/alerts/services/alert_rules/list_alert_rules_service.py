# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository


class ListAlertRulesService:

    def __init__(self, repo: AlertRuleRepository):
        self._repo = repo

    def list(self, user_id: int | None = None, is_admin: bool = False) -> ServiceResult[list[AlertRule]]:
        if is_admin:
            rules = self._repo.list_all()
        elif user_id is not None:
            rules = self._repo.list_by_user(user_id)
        else:
            rules = []
        return ServiceResult.ok(data=rules)
