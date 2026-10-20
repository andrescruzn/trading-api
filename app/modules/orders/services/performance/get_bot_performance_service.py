# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/performance/get_bot_performance_service.py
#
# CASO DE USO:
# - Rendimiento de un agente: operaciones cerradas y sus métricas
#   (domain/performance.py) más el P&L no realizado de la posición
#   abierta, valorada al último cierre.
#
# REGLAS:
# - Un usuario solo ve los agentes de sus cuentas (el admin, cualquiera);
#   un agente ajeno responde BOT_NOT_FOUND.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.performance import Performance, compute_performance


@dataclass
class BotPerformance:
    performance: Performance
    last_price: Decimal | None
    unrealized_pnl: Decimal | None


class GetBotPerformanceService:
    """Métricas de rendimiento de un agente."""

    def __init__(
        self,
        fill_repo: FillRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        candle_repo: CandleRepository,
    ):
        self._fill_repo = fill_repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._candle_repo = candle_repo

    def get(self, bot_id: int, owner_id: int | None = None) -> ServiceResult[BotPerformance]:
        bot = find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        fills = self._fill_repo.list_trade_fills_by_bots([bot.id]).get(bot.id, [])
        performance = compute_performance(fills)

        last_price: Decimal | None = None
        unrealized: Decimal | None = None
        if performance.open_qty > Decimal("0"):
            candles = self._candle_repo.list_candles(
                symbol_id=bot.symbol_id, timeframe_id=bot.timeframe_id, limit=1
            )
            if candles:
                last_price = Decimal(str(candles[0].close))
                unrealized = (last_price - performance.open_avg_price) * performance.open_qty

        return ServiceResult.ok(
            data=BotPerformance(
                performance=performance, last_price=last_price, unrealized_pnl=unrealized
            )
        )
