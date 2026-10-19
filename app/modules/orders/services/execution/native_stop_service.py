# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/execution/native_stop_service.py
#
# PROPÓSITO:
# - Stop loss NATIVO en live: al abrir una posición desde una señal, el SL
#   queda como orden en el exchange y protege aunque la API o el scheduler
#   estén caídos. El take profit lo sigue vigilando el scheduler.
#
# REGLAS:
# - place(): crea la Order (type=stop, side=sell, reason=stop_loss_native)
#   con su client_order_id, la persiste ANTES de enviarla y la vincula a la
#   posición (positions.sl_order_id). Si el exchange no lo soporta o la
#   rechaza → fail: la protección del scheduler queda de respaldo.
# - cancel(): antes de cualquier otra venta de la posición (manual, señal
#   SELL o take profit) hay que cancelar el SL nativo; si no, el exchange
#   podría vender dos veces. Si ya no está abierto (se ejecutó) → fail
#   ORDER_NATIVE_STOP_ACTIVE: la reconciliación actualizará la posición.
# ======================================================================

from __future__ import annotations

import logging
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils.datetime_utils import utc_now
from app.modules.bots.domain.bot_entity import Bot
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor

logger = logging.getLogger(__name__)


class NativeStopService:
    """Coloca y cancela el stop loss nativo de una posición live."""

    def __init__(
        self,
        order_repo: OrderRepository,
        position_repo: PositionRepository,
        symbol_repo: SymbolRepository,
        live_executor: LiveExecutor,
    ):
        self._order_repo = order_repo
        self._position_repo = position_repo
        self._symbol_repo = symbol_repo
        self._live = live_executor

    def place(
        self, bot: Bot, position: Position, stop_price: Decimal
    ) -> ServiceResult[Order]:
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        order = self._order_repo.create(
            Order(
                id=0,
                bot_id=bot.id,
                side="sell",
                type="stop",
                qty=position.qty,
                status="new",
                stop_price=stop_price,
                meta={"symbol": symbol.symbol, "mode": bot.mode, "reason": "stop_loss_native"},
                ts=utc_now(),
            )
        )
        order.client_order_id = Order.build_client_order_id(order.id)
        order = self._order_repo.update(order)
        self._order_repo.commit()

        try:
            result = self._live.place_stop_loss(order, bot)
        except ExecutionUncertainError as exc:
            # Pudo quedar en el exchange: se vincula y la reconciliación decide
            order.status = "sent"
            order.meta = {**order.meta, "needs_reconciliation": True, "error": str(exc)}
            self._order_repo.update(order)
            self._link(position, order.id)
            self._order_repo.commit()
            return ServiceResult.ok(data=order)
        except RuntimeError as exc:
            order.status = "rejected"
            order.meta = {**order.meta, "error": str(exc)}
            self._order_repo.update(order)
            self._order_repo.commit()
            logger.warning("SL nativo no colocado — bot=%d: %s", bot.id, exc)
            return ServiceResult.fail(
                code="NATIVE_STOP_FAILED", http_status=502, meta={"order_id": order.id}
            )

        order.status = result.status
        order.exchange_order_id = result.exchange_order_id
        order = self._order_repo.update(order)
        self._link(position, order.id)
        self._order_repo.commit()
        return ServiceResult.ok(data=order)

    def cancel(self, bot: Bot, position: Position) -> ServiceResult[None]:
        """Cancela el SL nativo de la posición (sin commit: lo hace el llamador)."""
        if position.sl_order_id is None:
            return ServiceResult.ok(data=None)

        stop_order = self._order_repo.get_by_id(position.sl_order_id)
        if stop_order is None or stop_order.status in ("canceled", "rejected"):
            self._link(position, None)
            return ServiceResult.ok(data=None)
        if stop_order.status == "filled":
            return ServiceResult.fail(code="ORDER_NATIVE_STOP_ACTIVE", http_status=409)

        try:
            canceled = self._live.cancel(stop_order, bot)
        except (ExecutionUncertainError, RuntimeError) as exc:
            logger.warning("No se pudo cancelar el SL nativo — bot=%d: %s", bot.id, exc)
            return ServiceResult.fail(code="ORDER_NATIVE_STOP_ACTIVE", http_status=409)

        if not canceled:
            # Ya no está abierta en el exchange: probablemente se ejecutó
            return ServiceResult.fail(code="ORDER_NATIVE_STOP_ACTIVE", http_status=409)

        stop_order.status = "canceled"
        self._order_repo.update(stop_order)
        self._link(position, None)
        return ServiceResult.ok(data=None)

    def _link(self, position: Position, order_id: int | None) -> None:
        position.sl_order_id = order_id
        self._position_repo.update(position)
