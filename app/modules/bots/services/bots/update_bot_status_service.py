# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/update_bot_status_service.py
#
# Gestiona las transiciones de estado de un bot (start/pause/stop/error).
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class UpdateBotStatusService:
    """
    Cambia el estado de un bot respetando las transiciones válidas.

    Transiciones permitidas (definidas en BotEntity):
        stopped  → running
        running  → paused, stopped, error
        paused   → running, stopped
        error    → stopped

    Efectos colaterales:
    - Al pasar a 'running'  → se registra started_at con timestamp UTC.
    - Al pasar a 'stopped'  → se registra stopped_at con timestamp UTC.
    - Al pasar a 'paused'   → no se modifica started_at ni stopped_at.
    - Al pasar a 'error'    → no se modifica started_at ni stopped_at.
    """

    def __init__(self, repo: BotRepository, session: Session):
        self._repo = repo
        self._session = session

    def transition(self, bot_id: int, new_status: str) -> ServiceResult[Bot]:
        bot = self._repo.get_by_id(bot_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if new_status not in Bot.VALID_STATUSES:
            return ServiceResult.fail(code="BOT_INVALID_STATUS", http_status=422)

        if not bot.can_transition_to(new_status):
            return ServiceResult.fail(
                code="BOT_INVALID_TRANSITION",
                http_status=409,
                meta={"current": bot.status, "requested": new_status},
            )

        now = datetime.now(tz=timezone.utc)

        if new_status == "running":
            bot.started_at = now
        elif new_status == "stopped":
            bot.stopped_at = now

        bot.status = new_status

        updated = self._repo.update(bot)
        self._session.commit()
        return ServiceResult.ok(data=updated)
