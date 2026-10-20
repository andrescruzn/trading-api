# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/execution/reconcile_orders_service.py
#
# PROPÓSITO:
# - Poner al día las órdenes live que quedaron abiertas en el sistema
#   (lo llama el scheduler en cada ciclo):
#   - límites / stops en el libro que se ejecutaron después,
#   - el stop loss nativo de una posición cuando el exchange lo dispara,
#   - órdenes con `needs_reconciliation` (timeout al enviarlas).
#
# REGLAS:
# - Se registra solo lo NUEVO: ejecutado según el exchange − fills ya
#   guardados. El fill nuevo se aplica a la posición (position_updater).
# - Estado: el del exchange (filled, partially_filled, sent, canceled,
#   rejected). Una orden con needs_reconciliation que el exchange no conoce
#   a los 10 minutos se marca rejected: nunca llegó.
# - Si es el SL nativo de la posición y terminó, se desvincula.
# - Compra con protección pendiente (`meta.protection`: no se ejecutó al
#   enviarla): al registrar su fill se ponen SL/TP en la posición y, en
#   live, el SL nativo. Si la orden es de una señal, su decisión pasa de
#   `executing` a `executed` (se ejecutó algo) o `failed` (terminó sin
#   ejecutarse).
# - Errores de red: se reintenta en el siguiente ciclo. Una orden por
#   commit: un fallo no deshace las demás.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.common.contracts import ServiceResult
from app.common.utils.datetime_utils import ensure_aware_utc, utc_now
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor
from app.modules.orders.services.orders.position_updater import apply_fill

if TYPE_CHECKING:
    from app.modules.alerts.services.evaluation.evaluate_alerts_service import EvaluateAlertsService
    from app.modules.orders.services.execution.native_stop_service import NativeStopService

logger = logging.getLogger(__name__)

# Ventana de órdenes a revisar y gracia antes de dar por perdida una orden
_LOOKBACK = timedelta(days=7)
_LOST_AFTER = timedelta(minutes=10)
_FINAL = ("filled", "canceled", "rejected")


@dataclass
class ReconcileReport:
    checked: int = 0
    updated: list[dict] = field(default_factory=list)


class ReconcileOrdersService:
    """Sincroniza con el exchange las órdenes live que siguen abiertas."""

    def __init__(
        self,
        order_repo: OrderRepository,
        fill_repo: FillRepository,
        position_repo: PositionRepository,
        bot_repo: BotRepository,
        live_executor: LiveExecutor,
        evaluate_alerts: "EvaluateAlertsService | None" = None,
        signal_repo: SignalRepository | None = None,
        native_stop: "NativeStopService | None" = None,
    ):
        self._order_repo = order_repo
        self._fill_repo = fill_repo
        self._position_repo = position_repo
        self._bot_repo = bot_repo
        self._live = live_executor
        self._evaluate_alerts = evaluate_alerts
        self._signal_repo = signal_repo
        self._native_stop = native_stop

    def run(self, limit: int = 50) -> ServiceResult[ReconcileReport]:
        report = ReconcileReport()
        now = utc_now()

        for order in self._order_repo.list_open_live(since=now - _LOOKBACK, limit=limit):
            report.checked += 1
            try:
                change = self._reconcile(order, now)
            except Exception:
                self._order_repo.rollback()
                logger.exception("[Reconcile] Error — order=%d", order.id)
                continue
            if change:
                report.updated.append({"order_id": order.id, **change})

        return ServiceResult.ok(data=report)

    def sync_one(self, order: Order) -> dict | None:
        """
        Sincroniza una sola orden ahora (p. ej. justo después de cancelarla,
        para registrar lo que se ejecutó desde el último ciclo). None si no
        cambió nada o el exchange no respondió (lo retoma el siguiente ciclo).
        """
        return self._reconcile(order, utc_now())

    # ------------------------------------------------------------------

    def _reconcile(self, order: Order, now) -> dict | None:
        bot = self._bot_repo.get_by_id(order.bot_id)
        if bot is None:
            return None

        try:
            remote = self._live.fetch(order, bot)
        except ExecutionUncertainError:
            return None  # red: se reintenta en el siguiente ciclo
        except RuntimeError as exc:
            logger.warning("[Reconcile] No se pudo consultar order=%d: %s", order.id, exc)
            return None

        previous_status = order.status
        needs_reconciliation = bool(order.meta.get("needs_reconciliation"))

        if remote is None:
            age = now - (ensure_aware_utc(order.ts) or now)
            if not needs_reconciliation or age < _LOST_AFTER:
                return None
            order.status = "rejected"
            order.meta = {
                **{k: v for k, v in order.meta.items() if k != "needs_reconciliation"},
                "error": "La orden no llegó al exchange.",
            }
            self._finish(order, bot, filled_delta=None)
            return {"status": order.status, "previous": previous_status}

        try:
            result = LiveExecutor._to_result(order, remote)
        except ExecutionUncertainError:
            return None  # ejecución sin precio: se reintenta

        if result.exchange_order_id and not order.exchange_order_id:
            order.exchange_order_id = result.exchange_order_id

        delta = self._new_fill(order, result.fill)
        order.status = result.status
        # Ejecutada en parte y luego cerrada (cancelada/vencida): estado final
        if result.status == "partially_filled" and str(remote.get("status") or "") in (
            "canceled", "cancelled", "expired", "rejected",
        ):
            order.status = "canceled"
        if needs_reconciliation:
            order.meta = {k: v for k, v in order.meta.items() if k != "needs_reconciliation"}

        if delta is None and order.status == previous_status and not needs_reconciliation:
            return None

        self._finish(order, bot, filled_delta=delta)
        return {
            "status": order.status,
            "previous": previous_status,
            "filled": str(delta.qty) if delta else "0",
        }

    def _new_fill(self, order: Order, total: Fill | None) -> Fill | None:
        """Fill con lo ejecutado que aún no estaba registrado (None si nada nuevo)."""
        if total is None:
            return None
        recorded = self._fill_repo.list_by_order(order_id=order.id)
        recorded_qty = sum((f.qty for f in recorded), Decimal("0"))
        recorded_fee = sum((f.fee or Decimal("0") for f in recorded), Decimal("0"))
        delta_qty = total.qty - recorded_qty
        if delta_qty <= Decimal("0"):
            return None
        total.qty = delta_qty
        total.fee = max((total.fee or Decimal("0")) - recorded_fee, Decimal("0"))
        total.order_id = order.id
        return total

    def _finish(self, order: Order, bot, filled_delta: Fill | None) -> None:
        position = self._position_repo.get_by_bot_and_symbol(bot.id, bot.symbol_id)

        if filled_delta is not None:
            self._fill_repo.create(filled_delta)
            position = apply_fill(
                self._position_repo,
                bot=bot,
                position=position,
                fill_qty=filled_delta.qty,
                fill_price=filled_delta.price,
                side=order.side,
            )

        # El SL nativo terminó (ejecutado, cancelado o rechazado): desvincular
        if position is not None and position.sl_order_id == order.id and order.status in _FINAL:
            position.sl_order_id = None
            self._position_repo.update(position)

        # La protección pendiente va en el MISMO commit que el fill: si se
        # aplicara después y fallara, la orden ya sería final y la
        # reconciliación no volvería a verla (posición sin protección).
        native_stop_price = None
        if filled_delta is not None and order.side == "buy":
            native_stop_price = self._apply_pending_protection(order, position)

        self._order_repo.update(order)
        self._order_repo.commit()

        if native_stop_price is not None:
            self._place_native_stop(order, bot, position, native_stop_price)
        self._settle_signal(order)

        if order.status == "rejected" and self._evaluate_alerts is not None:
            try:
                self._evaluate_alerts.evaluate_order_alerts(order=order, bot_id=bot.id)
            except Exception:
                pass

    def _apply_pending_protection(self, order: Order, position) -> Decimal | None:
        """
        SL/TP que la compra traía y no se pudieron poner al enviarla (sin
        commit: va con el del fill). Devuelve el SL a dejar como orden nativa.
        """
        pending = order.meta.get("protection")
        if not pending or pending.get("applied") or position is None or position.is_flat():
            return None

        stop_loss = Decimal(pending["stop_loss"]) if pending.get("stop_loss") else None
        take_profit = Decimal(pending["take_profit"]) if pending.get("take_profit") else None
        position.set_protection(
            stop_loss if stop_loss is not None else position.stop_loss,
            take_profit if take_profit is not None else position.take_profit,
            signal_id=order.signal_id or position.signal_id,
        )
        self._position_repo.update(position)
        order.meta = {**order.meta, "protection": {**pending, "applied": True}}
        return stop_loss

    def _place_native_stop(self, order: Order, bot, position, stop_loss: Decimal) -> None:
        """
        SL nativo en live. `native_stop` solo se inyecta con
        ORDER_NATIVE_STOP_LOSS=true (order_provider); si falla, el scheduler
        vigila el SL que ya quedó en la posición.
        """
        if bot.mode == "live" and self._native_stop is not None and not position.has_native_stop():
            placed = self._native_stop.place(bot, position, stop_loss)
            if not placed.success:
                logger.warning(
                    "[Reconcile] SL nativo no colocado — order=%d: %s", order.id, placed.error.code
                )

    def _settle_signal(self, order: Order) -> None:
        """Cierra la decisión de la señal cuya orden quedó sin confirmar."""
        if self._signal_repo is None or order.signal_id is None:
            return
        if order.status in ("filled", "partially_filled") or (
            order.status == "canceled" and self._fill_repo.list_by_order(order_id=order.id)
        ):
            to_status, reason = "executed", None
        elif order.status in ("rejected", "canceled"):
            to_status, reason = "failed", "ORDER_EXECUTION_FAILED"
        else:
            return
        fields = {"decision_reason": reason} if reason else {}
        if self._signal_repo.transition_decision(
            order.signal_id, from_statuses=("executing",), to_status=to_status, **fields
        ):
            self._signal_repo.commit()

