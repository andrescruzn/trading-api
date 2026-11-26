# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/get_bot_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.bots.services.bots.demo_capital import attach_demo_capital


class GetBotService:
    """Obtiene un bot por su ID. Un usuario solo ve los de sus cuentas."""

    def __init__(self, repo: BotRepository, account_repo: AccountRepository):
        self._repo = repo
        self._account_repo = account_repo

    def get(self, bot_id: int, owner_id: int | None = None) -> ServiceResult[Bot]:
        bot = find_accessible_bot(self._repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)
        attach_demo_capital([bot], self._account_repo)
        return ServiceResult.ok(data=bot)
