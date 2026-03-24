# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/get_bot_service.py
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class GetBotService:
    """Obtiene un bot por su ID."""

    def __init__(self, repo: BotRepository):
        self._repo = repo

    def get(self, bot_id: int) -> ServiceResult[Bot]:
        bot = self._repo.get_by_id(bot_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)
        return ServiceResult.ok(data=bot)
