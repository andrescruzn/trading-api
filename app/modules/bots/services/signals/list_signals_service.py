# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/signals/list_signals_service.py
# ======================================================================

from __future__ import annotations

from datetime import datetime

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot


class ListSignalsService:
    """Lista signals de un bot con filtros opcionales (solo bots propios, salvo admin)."""

    def __init__(
        self,
        repo: SignalRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def list(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
        owner_id: int | None = None,
    ) -> ServiceResult[list[Signal]]:
        if find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id) is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if action is not None and action not in Signal.VALID_ACTIONS:
            return ServiceResult.fail(code="SIGNAL_INVALID_ACTION_FILTER", http_status=422)

        signals = self._repo.list_by_bot(
            bot_id=bot_id,
            action=action,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=min(limit, 500),
        )
        return ServiceResult.ok(data=signals)
