# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/domain/alert_rule_repository.py
#
# Contrato (Protocol) del repositorio de AlertRules.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.modules.alerts.domain.alert_rule_entity import AlertRule


class AlertRuleRepository(Protocol):

    def list_by_user(self, user_id: int) -> list[AlertRule]: ...

    def list_all(self) -> list[AlertRule]: ...

    def list_active_by_type_and_bot(
        self, rule_type: str, bot_id: int | None = None
    ) -> list[AlertRule]: ...

    def get_by_id(self, rule_id: int) -> AlertRule | None: ...

    def create(self, rule: AlertRule) -> AlertRule: ...

    def update(self, rule: AlertRule) -> AlertRule: ...
