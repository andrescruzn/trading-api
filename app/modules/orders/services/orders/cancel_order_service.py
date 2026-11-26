# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/cancel_order_service.py
#
# CASO DE USO:
# - Cancelar una orden live que sigue abierta en el exchange (límite o
#   stop sin ejecutar, o ejecutada en parte).
#
# REGLAS:
# - Solo órdenes `sent` / `partially_filled` de agentes del usuario (el
#   admin, de cualquiera). En paper las órdenes se ejecutan al instante:
#   nunca quedan abiertas.
# - Sin `exchange_order_id` (timeout al enviarla) no se puede cancelar
#   todavía: la reconciliación tiene que encontrarla primero.
# - Tras cancelar se sincroniza la orden con el exchange (misma lógica de
#   la reconciliación) para registrar lo que se ejecutó desde el último
#   ciclo; si el exchange no responde, `meta.cancel_requested` y el
#   siguiente ciclo la deja en su estado final.
# - Cancelar el stop loss nativo deja la posición con su SL guardado: la
#   vuelve a vigilar el scheduler (la reconciliación desvincula la orden).
# - No pasa por el RiskGate: cancelar reduce riesgo y siempre se permite.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor
from app.modules.orders.services.execution.reconcile_orders_service import (
    ReconcileOrdersService,
)

_CANCELABLE = ("sent", "partially_filled")


class CancelOrderService:
    """Cancela una orden live abierta y la sincroniza con el exchange."""

    def __init__(
        self,
        order_repo: OrderRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        live_executor: LiveExecutor,
        reconcile: ReconcileOrdersService,
    ):
        self._order_repo = order_repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._live = live_executor
        self._reconcile = reconcile

    def cancel(self, order_id: int, owner_id: int | None = None) -> ServiceResult[Order]:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)

        bot = find_accessible_bot(self._bot_repo, self._account_repo, order.bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)

        if order.status not in _CANCELABLE or order.meta.get("mode", bot.mode) != "live":
            return ServiceResult.fail(
                code="ORDER_NOT_CANCELABLE",
                http_status=409,
                meta={"status": order.status},
            )

        if not order.exchange_order_id:
            return ServiceResult.fail(code="ORDER_CANCEL_PENDING_SYNC", http_status=409)

        try:
            self._live.cancel(order, bot)
        except ExecutionUncertainError:
            return ServiceResult.fail(
                code="ORDER_CANCEL_UNCERTAIN", http_status=502, meta={"order_id": order.id}
            )
        except RuntimeError:
            return ServiceResult.fail(
                code="ORDER_CANCEL_FAILED", http_status=502, meta={"order_id": order.id}
            )

        # Cancelada o ya cerrada en el exchange: lo que diga el exchange manda
        # (fills nuevos incluidos). Si no responde, el siguiente ciclo lo cierra.
        change = self._reconcile.sync_one(order)
        if change is None and order.status in _CANCELABLE:
            order.meta = {**order.meta, "cancel_requested": True}
            order = self._order_repo.update(order)
            self._order_repo.commit()

        return ServiceResult.ok(data=order)
