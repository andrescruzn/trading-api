# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/execution/protect_positions_service.py
#
# PROPÓSITO:
# - Cerrar a mercado las posiciones cuya última vela tocó el stop loss o
#   el take profit guardados al ejecutar la señal (lo llama el scheduler).
#
# REGLAS:
# - Solo largos (spot). Si la vela toca SL y TP, gana el SL (peor caso).
# - Actúa aunque el agente esté pausado o detenido: proteger el capital
#   no depende de que el agente siga buscando entradas. El kill switch
#   global (TRADING_ENABLED) sí lo detiene.
# - Se mira la vela más reciente (también la que está en formación): su
#   high/low ya refleja si el precio cruzó el nivel.
#
# LIMITACIÓN:
# - Es una protección "por ciclo" (cada SCHEDULER_INTERVAL_SECONDS), no una
#   orden stop en el exchange: en live, un movimiento brusco puede cerrar
#   más lejos del nivel. Mejora futura: órdenes stop/OCO nativas.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.services.orders.create_order_service import CreateOrderService

logger = logging.getLogger(__name__)


@dataclass
class ProtectionReport:
    checked: int = 0
    closed: list[dict] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)


class ProtectPositionsService:
    """Cierra posiciones que tocaron su stop loss o take profit."""

    def __init__(
        self,
        position_repo: PositionRepository,
        bot_repo: BotRepository,
        candle_repo: CandleRepository,
        create_order: CreateOrderService,
    ):
        self._position_repo = position_repo
        self._bot_repo = bot_repo
        self._candle_repo = candle_repo
        self._create_order = create_order

    def run(self) -> ServiceResult[ProtectionReport]:
        report = ProtectionReport()

        for position in self._position_repo.list_protected():
            report.checked += 1
            bot = self._bot_repo.get_by_id(position.bot_id)
            if bot is None:
                continue

            candles = self._candle_repo.list_candles(
                symbol_id=position.symbol_id,
                timeframe_id=bot.timeframe_id,
                limit=1,
            )
            if not candles:
                continue

            candle = candles[0]
            hit = position.protection_hit(
                low=Decimal(str(candle.low)),
                high=Decimal(str(candle.high)),
            )
            if hit is None:
                continue

            result = self._create_order.create(
                bot_id=bot.id,
                side="sell",
                order_type="market",
                qty=position.qty,
                owner_id=None,
                require_running=False,
                reason=hit,
            )
            entry = {"bot_id": bot.id, "position_id": position.id, "reason": hit}
            if result.success:
                report.closed.append({**entry, "order_id": result.data.id})
                logger.info("[Protect] Posición cerrada por %s — bot=%d", hit, bot.id)
            else:
                report.failed.append({**entry, "code": result.error.code})
                logger.warning(
                    "[Protect] No se pudo cerrar por %s — bot=%d code=%s",
                    hit, bot.id, result.error.code,
                )

        return ServiceResult.ok(data=report)
