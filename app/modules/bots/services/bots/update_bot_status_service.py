# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/update_bot_status_service.py
#
# Gestiona las transiciones de estado de un bot (start/pause/stop/error).
# ======================================================================

from __future__ import annotations


from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.common.utils import utc_now
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot


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

    def __init__(self, repo: BotRepository, account_repo: AccountRepository):
        self._repo = repo
        self._account_repo = account_repo

    def transition(
        self,
        bot_id: int,
        new_status: str,
        owner_id: int | None = None,
    ) -> ServiceResult[Bot]:
        """`owner_id=None` = sin restricción de propiedad (admin)."""
        bot = find_accessible_bot(self._repo, self._account_repo, bot_id, owner_id)
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

        now = utc_now()

        if new_status == "running":
            bot.started_at = now
        elif new_status == "stopped":
            bot.stopped_at = now

        bot.status = new_status

        updated = self._repo.update(bot)
        self._repo.commit()
        return ServiceResult.ok(data=updated)
