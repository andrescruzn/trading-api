# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/signals/list_pending_signals_service.py
#
# Lista las señales que esperan aprobación (decision_status = pending) de
# los agentes del usuario, con su agente, para la cola del dashboard.
# Las vencidas que el scheduler aún no marcó se excluyen.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository


@dataclass(frozen=True)
class PendingSignal:
    signal: Signal
    bot: Bot


class ListPendingSignalsService:
    """Señales por aprobar de los agentes del usuario (admin: `mine` o todas)."""

    def __init__(
        self,
        repo: SignalRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def list(self, owner_id: int | None = None, limit: int = 50) -> ServiceResult[list[PendingSignal]]:
        if owner_id is None:
            bots = self._bot_repo.list_all()
        else:
            account_ids = [a.id for a in self._account_repo.list_by_user_id(owner_id)]
            bots = self._bot_repo.list_by_account_ids(account_ids)

        bots_by_id = {bot.id: bot for bot in bots}
        signals = self._repo.list_by_decision_status(
            "pending",
            bot_ids=list(bots_by_id),
            limit=limit,
        )

        now = utc_now()
        pending = [
            PendingSignal(signal=signal, bot=bots_by_id[signal.bot_id])
            for signal in signals
            if signal.bot_id in bots_by_id and not signal.is_expired_at(now)
        ]
        return ServiceResult.ok(data=pending)
