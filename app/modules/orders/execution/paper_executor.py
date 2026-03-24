# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/execution/paper_executor.py
#
# Ejecutor de órdenes en modo paper (simulado).
#
# Lógica de simulación:
# - Usa el precio `close` de la última vela disponible como precio
#   de ejecución (precio de mercado simulado).
# - Si la orden es de tipo `limit`, usa el precio límite como precio
#   de ejecución (asume que se ejecutó al precio deseado).
# - Comisión = 0 (modo paper no cobra fees).
# - exchange_trade_id = None (no hay ID real de exchange).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.utils.datetime_utils import utc_now
from app.modules.bots.domain.bot_entity import Bot
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import ExecutorInterface


class PaperExecutor(ExecutorInterface):
    """
    Ejecuta órdenes en modo simulado (paper trading).

    Determina el precio de ejecución así:
    - market    → último precio close de vela en BD
    - limit     → precio límite de la orden (asumimos ejecución inmediata)
    - stop      → stop_price de la orden
    - stop_limit→ precio límite de la orden

    No hay llamadas a exchanges externos ni comisiones reales.
    """

    def __init__(self, candle_repo: CandleRepository):
        self._candle_repo = candle_repo

    def execute(self, order: Order, bot: Bot) -> Fill:
        """
        Simula la ejecución de la orden y retorna el Fill resultante.

        El precio de ejecución depende del tipo de orden:
        - market: precio de la última vela close (más realista)
        - limit / stop_limit: usa order.price (ejecuta al precio deseado)
        - stop: usa order.stop_price como precio de activación

        Raises:
            RuntimeError: si no hay velas disponibles para resolver
                          el precio de mercado (solo para market orders).
        """
        execution_price = self._resolve_price(order, bot)
        now = utc_now()

        return Fill(
            id=0,                            # el repo asignará el ID real
            order_id=order.id,
            exchange_trade_id=None,          # no existe en modo paper
            qty=order.qty,
            price=execution_price,
            fee=Decimal("0"),                # sin comisión en paper
            fee_asset=None,
            ts=now,
            created_at=now,
        )

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _resolve_price(self, order: Order, bot: Bot) -> Decimal:
        """
        Determina el precio de ejecución según el tipo de orden.

        Para market orders consulta la última vela en BD.
        Para el resto usa el precio ya definido en la orden.
        """
        if order.type == "market":
            return self._get_last_close(bot)

        if order.type in ("limit", "stop_limit") and order.price is not None:
            return order.price

        if order.type == "stop" and order.stop_price is not None:
            return order.stop_price

        # Fallback: intentar precio de mercado si no hay precio definido
        return self._get_last_close(bot)

    def _get_last_close(self, bot: Bot) -> Decimal:
        """
        Obtiene el precio close de la última vela disponible para
        el símbolo y timeframe del bot.

        Raises:
            RuntimeError: si no hay velas en BD para este símbolo/timeframe.
        """
        candles = self._candle_repo.list_candles(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            limit=1,
        )

        if not candles:
            raise RuntimeError(
                f"No hay velas disponibles para simular el precio de mercado. "
                f"symbol_id={bot.symbol_id}, timeframe_id={bot.timeframe_id}. "
                f"Ingresa velas primero via POST /candles/ingest."
            )

        return candles[0].close
