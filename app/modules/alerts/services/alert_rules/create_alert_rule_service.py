# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot


class CreateAlertRuleService:
    """
    Crea una regla de alerta.

    Reglas de negocio:
    - El bot vigilado debe ser del usuario (si no, recibiría señales ajenas).
    - El webhook, si viene, debe ser https y no apuntar a la red interna.
    """

    def __init__(
        self,
        repo: AlertRuleRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def create(
        self,
        name: str,
        rule_type: str,
        rule_spec: dict[str, Any],
        channels: dict[str, Any],
        user_id: int | None = None,
        bot_id: int | None = None,
        owner_id: int | None = None,
    ) -> ServiceResult[AlertRule]:
        if rule_type not in AlertRule.VALID_TYPES:
            return ServiceResult.fail(
                code="ALERT_RULE_INVALID_TYPE",
                http_status=422,
                meta={"rule_type": rule_type},
            )

        if bot_id is not None and find_accessible_bot(
            self._bot_repo, self._account_repo, bot_id, owner_id
        ) is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

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

        if not rule.has_valid_webhook():
            return ServiceResult.fail(code="ALERT_RULE_INVALID_WEBHOOK", http_status=422)

        created = self._repo.create(rule)
        self._repo.commit()
        return ServiceResult.ok(data=created)
