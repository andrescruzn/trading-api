# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/agent_info.py
#
# PROPÓSITO:
# - Datos públicos de un agente para las vistas del fondo (nombre, estado,
#   modo y mercado). Nunca la cuenta ni sus credenciales: el inversor ve el
#   agente en el que participa, no la billetera.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.market.domain.symbol_repository import SymbolRepository


@dataclass(frozen=True)
class AgentInfo:
    bot_id: int
    name: str
    status: str
    mode: str
    symbol: str | None


class AgentInfoReader:

    def __init__(self, bot_repo: BotRepository, symbol_repo: SymbolRepository):
        self._bot_repo = bot_repo
        self._symbol_repo = symbol_repo

    def bot(self, bot_id: int) -> Bot | None:
        return self._bot_repo.get_by_id(bot_id)

    def info(self, bot: Bot) -> AgentInfo:
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        return AgentInfo(
            bot_id=bot.id,
            name=bot.name,
            status=bot.status,
            mode=bot.mode,
            symbol=symbol.symbol if symbol else None,
        )

    def info_by_id(self, bot_id: int) -> AgentInfo | None:
        bot = self.bot(bot_id)
        return None if bot is None else self.info(bot)
