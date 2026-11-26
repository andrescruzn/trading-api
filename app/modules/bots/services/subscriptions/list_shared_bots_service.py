# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/subscriptions/list_shared_bots_service.py
#
# PROPÓSITO:
# - Lista los agentes que comparten sus señales (share_signals = True)
#   con lo que puede ver cualquier usuario: estrategia, mercado, modo,
#   estado y número de suscriptores; además, si quien consulta ya lo sigue
#   y si el agente es suyo.
#
# NOTAS:
# - Nunca expone la cuenta, el capital, el nombre del agente ni al dueño:
#   el nombre lo escribe la persona y puede identificarla.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_subscription_repository import (
    SignalSubscriptionRepository,
)
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.strategies.domain.strategy_repository import StrategyRepository


@dataclass(frozen=True)
class SharedBot:
    """Vista pública de un agente compartido."""

    bot_id: int
    strategy_id: int
    strategy_name: str | None
    symbol_id: int
    symbol: str | None
    timeframe_id: int
    timeframe: str | None
    mode: str
    status: str
    subscribers_count: int
    is_subscribed: bool
    is_mine: bool


class ListSharedBotsService:
    """
    Lista los agentes compartidos para un usuario.

    Reglas de negocio:
    - Solo agentes con share_signals = True (de cualquier dueño).
    - `is_mine` = el agente es de una cuenta del usuario (no puede seguirlo).
    """

    def __init__(
        self,
        bot_repo: BotRepository,
        subscription_repo: SignalSubscriptionRepository,
        account_repo: AccountRepository,
        strategy_repo: StrategyRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
    ):
        self._bot_repo = bot_repo
        self._subscription_repo = subscription_repo
        self._account_repo = account_repo
        self._strategy_repo = strategy_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo

    def list(self, user_id: int) -> ServiceResult[list[SharedBot]]:
        bots = self._bot_repo.list_shared()
        if not bots:
            return ServiceResult.ok(data=[])

        own_account_ids = {a.id for a in self._account_repo.list_by_user_id(user_id)}
        followed = set(self._subscription_repo.list_bot_ids_by_user(user_id))
        counts = self._subscription_repo.count_by_bot_ids([b.id for b in bots])

        # Varios agentes comparten estrategia, símbolo o timeframe: una
        # consulta por ID distinto, no una por agente
        strategies: dict[int, str | None] = {}
        symbols: dict[int, str | None] = {}
        timeframes: dict[int, str | None] = {}

        items: list[SharedBot] = []
        for bot in bots:
            if bot.strategy_id not in strategies:
                strategy = self._strategy_repo.get_by_id(bot.strategy_id)
                strategies[bot.strategy_id] = strategy.name if strategy else None
            if bot.symbol_id not in symbols:
                symbol = self._symbol_repo.get_by_id(bot.symbol_id)
                symbols[bot.symbol_id] = symbol.symbol if symbol else None
            if bot.timeframe_id not in timeframes:
                timeframe = self._timeframe_repo.get_by_id(bot.timeframe_id)
                timeframes[bot.timeframe_id] = timeframe.code if timeframe else None

            items.append(
                SharedBot(
                    bot_id=bot.id,
                    strategy_id=bot.strategy_id,
                    strategy_name=strategies[bot.strategy_id],
                    symbol_id=bot.symbol_id,
                    symbol=symbols[bot.symbol_id],
                    timeframe_id=bot.timeframe_id,
                    timeframe=timeframes[bot.timeframe_id],
                    mode=bot.mode,
                    status=bot.status,
                    subscribers_count=counts.get(bot.id, 0),
                    is_subscribed=bot.id in followed,
                    is_mine=bot.account_id in own_account_ids,
                )
            )
        return ServiceResult.ok(data=items)
