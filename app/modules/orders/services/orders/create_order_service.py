# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/create_order_service.py
#
# Crea y ejecuta una orden de trading — lógica central del Módulo 8.
#
# FLUJO COMPLETO:
#   1. Validar bot (existe, es del usuario, está running)
#   2. Validar parámetros de la orden (side, type, qty, price)
#   3. Validar la señal vinculada (del mismo bot, aprobada, misma dirección
#      y sin otra orden activa)
#   4. Precio de referencia y regla de spot: no vender más de lo que hay
#   5. RiskGate: kill switch, live apagado, notional máximo, drawdown
#   5b. Venta de una posición con SL nativo (live): cancelarlo primero
#   6. Persistir la Order (status="new") con su client_order_id y COMMIT:
#      la intención queda registrada antes de hablar con el exchange
#   7. Ejecutar (paper o live) y registrar el resultado REAL:
#      filled / partially_filled → Fill + Position; sent → solo la orden;
#      rechazo → rejected; sin respuesta → sent + needs_reconciliation
#   8. Commit y hook de alertas
#
# DECISIÓN DE DISEÑO — Persistir antes de enviar:
#   Si se revierte la orden cuando la llamada al exchange falla por red,
#   puede quedar una orden viva en el exchange que el sistema no conoce.
#   Por eso la orden se confirma primero y luego se actualiza con lo que
#   responda el exchange; los rechazos quedan como historial auditable.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.common.contracts import ServiceResult
from app.common.utils.datetime_utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.execution.executor_interface import (
    ExecutionUncertainError,
    ExecutorInterface,
)
from app.modules.orders.execution.live_executor import LiveExecutor
from app.modules.orders.execution.paper_executor import PaperExecutor
from app.modules.orders.services.orders.position_updater import apply_fill
from app.modules.orders.services.risk.risk_gate_service import RiskGateService

if TYPE_CHECKING:
    from app.modules.alerts.services.evaluation.evaluate_alerts_service import EvaluateAlertsService
    from app.modules.orders.services.execution.native_stop_service import NativeStopService


class CreateOrderService:
    """
    Crea y ejecuta una orden de trading.

    Reglas de negocio:
    - El bot debe ser del usuario (owner_id) y estar en estado 'running'.
    - side debe ser 'buy' o 'sell' (no 'hold' — hold = no operar).
    - type 'limit' y 'stop_limit' requieren price > 0.
    - type 'stop' y 'stop_limit' requieren stop_price > 0.
    - qty debe ser > 0. En spot no hay cortos: no se vende más de la posición.
    - signal_id, si viene: señal del mismo bot, aprobada, con la misma
      dirección y sin otra orden activa (una señal = una orden).
    - Toda orden pasa por el RiskGate antes de ejecutarse.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        fill_repo: FillRepository,
        position_repo: PositionRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        signal_repo: SignalRepository,
        symbol_repo: SymbolRepository,
        candle_repo: CandleRepository,
        risk_gate: RiskGateService,
        paper_executor: PaperExecutor,
        live_executor: LiveExecutor,
        evaluate_alerts: "EvaluateAlertsService | None" = None,
        native_stop: "NativeStopService | None" = None,
    ):
        self._native_stop = native_stop
        self._order_repo = order_repo
        self._fill_repo = fill_repo
        self._position_repo = position_repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._signal_repo = signal_repo
        self._symbol_repo = symbol_repo
        self._candle_repo = candle_repo
        self._risk_gate = risk_gate
        self._paper_executor = paper_executor
        self._live_executor = live_executor
        self._evaluate_alerts = evaluate_alerts

    def create(
        self,
        bot_id: int,
        side: str,
        order_type: str,
        qty: Decimal,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        time_in_force: str | None = None,
        signal_id: int | None = None,
        owner_id: int | None = None,
        require_running: bool = True,
        reason: str | None = None,
    ) -> ServiceResult[Order]:
        """
        Args:
            require_running: False solo para cerrar por stop loss / take profit:
                             la protección actúa aunque el agente esté pausado
                             o detenido (el kill switch global sigue aplicando).
            reason:          origen de la orden para el historial (`meta.reason`):
                             manual, signal, stop_loss, take_profit.
        """

        # ------------------------------------------------------------------
        # 1. Cargar y validar el bot (un usuario solo opera los suyos)
        # ------------------------------------------------------------------
        bot = find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if require_running and bot.status != "running":
            return ServiceResult.fail(
                code="BOT_NOT_RUNNING",
                http_status=409,
                meta={"status": bot.status},
            )

        # ------------------------------------------------------------------
        # 2. Validar parámetros de la orden
        # ------------------------------------------------------------------
        if side not in Order.VALID_SIDES:
            return ServiceResult.fail(
                code="ORDER_INVALID_SIDE",
                http_status=422,
                meta={"side": side},
            )

        if order_type not in Order.VALID_TYPES:
            return ServiceResult.fail(
                code="ORDER_INVALID_TYPE",
                http_status=422,
                meta={"type": order_type},
            )

        if qty <= Decimal("0"):
            return ServiceResult.fail(code="ORDER_INVALID_QTY", http_status=422)

        # Las órdenes limit y stop_limit requieren price
        if order_type in ("limit", "stop_limit") and (price is None or price <= Decimal("0")):
            return ServiceResult.fail(
                code="ORDER_PRICE_REQUIRED",
                http_status=422,
                meta={"type": order_type},
            )

        # Las órdenes stop y stop_limit requieren stop_price
        if order_type in ("stop", "stop_limit") and (stop_price is None or stop_price <= Decimal("0")):
            return ServiceResult.fail(
                code="ORDER_STOP_PRICE_REQUIRED",
                http_status=422,
                meta={"type": order_type},
            )

        # ------------------------------------------------------------------
        # 3. Señal vinculada
        # ------------------------------------------------------------------
        if signal_id is not None:
            signal_check = self._check_signal(signal_id, bot_id, side)
            if not signal_check.success:
                return signal_check

        # ------------------------------------------------------------------
        # 4. Símbolo, precio de referencia y regla de spot (sin cortos)
        # ------------------------------------------------------------------
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        reference_price = price or stop_price or self._last_close(bot)
        if reference_price is None:
            return ServiceResult.fail(code="ORDER_NO_MARKET_PRICE", http_status=422)

        position = self._position_repo.get_by_bot_and_symbol(
            bot_id=bot_id,
            symbol_id=bot.symbol_id,
        )
        if side == "sell":
            held = position.qty if position is not None else Decimal("0")
            if qty > held:
                return ServiceResult.fail(
                    code="ORDER_SELL_EXCEEDS_POSITION",
                    http_status=422,
                    meta={"held": str(held)},
                )

        # ------------------------------------------------------------------
        # 5. Salvaguardas del servidor
        # ------------------------------------------------------------------
        gate = self._risk_gate.check(bot=bot, side=side, qty=qty, reference_price=reference_price)
        if not gate.success:
            return ServiceResult.fail(
                code=gate.error.code,
                http_status=gate.error.http_status,
                meta=gate.error.meta,
            )

        # ------------------------------------------------------------------
        # 5b. Un SL nativo vivo vendería otra vez la misma posición: se
        #     cancela antes de cualquier otra venta
        # ------------------------------------------------------------------
        if (
            side == "sell"
            and position is not None
            and position.has_native_stop()
            and self._native_stop is not None
        ):
            canceled = self._native_stop.cancel(bot, position)
            if not canceled.success:
                return ServiceResult.fail(
                    code=canceled.error.code,
                    http_status=canceled.error.http_status,
                )

        # ------------------------------------------------------------------
        # 6. Persistir la intención antes de hablar con el exchange
        # ------------------------------------------------------------------
        order = self._order_repo.create(
            Order(
                id=0,
                bot_id=bot_id,
                signal_id=signal_id,
                side=side,
                type=order_type,
                qty=qty,
                status="new",
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
                # Guardamos el símbolo en meta para que LiveExecutor pueda usarlo
                meta={
                    "symbol": symbol.symbol,
                    "mode": bot.mode,
                    "reason": reason or ("signal" if signal_id else "manual"),
                },
                ts=utc_now(),
            )
        )
        order.client_order_id = Order.build_client_order_id(order.id)
        order = self._order_repo.update(order)
        self._order_repo.commit()

        # ------------------------------------------------------------------
        # 7. Ejecutar (patrón Strategy) y registrar el resultado real
        # ------------------------------------------------------------------
        executor: ExecutorInterface = (
            self._paper_executor if bot.mode == "paper" else self._live_executor
        )

        try:
            result = executor.execute(order, bot)
        except ExecutionUncertainError as exc:
            order.status = "sent"
            order.meta = {**order.meta, "needs_reconciliation": True, "error": str(exc)}
            self._order_repo.update(order)
            self._order_repo.commit()
            return ServiceResult.fail(
                code="ORDER_EXECUTION_UNCERTAIN",
                http_status=502,
                meta={"order_id": order.id},
            )
        except RuntimeError as exc:
            order.status = "rejected"
            order.meta = {**order.meta, "error": str(exc)}
            order = self._order_repo.update(order)
            self._order_repo.commit()
            self._fire_order_alerts(order, bot_id)
            return ServiceResult.fail(
                code="ORDER_EXECUTION_FAILED",
                http_status=502,
                meta={"order_id": order.id},
            )

        order.status = result.status
        order.exchange_order_id = result.exchange_order_id

        if result.fill is not None:
            fill = result.fill
            fill.order_id = order.id
            fill = self._fill_repo.create(fill)
            if order.exchange_order_id is None:
                order.exchange_order_id = fill.exchange_trade_id
            apply_fill(
                self._position_repo,
                bot=bot,
                position=position,
                fill_qty=fill.qty,
                fill_price=fill.price,
                side=side,
            )

        order = self._order_repo.update(order)

        # ------------------------------------------------------------------
        # 8. Commit — confirma estado + fill + position en la BD
        # ------------------------------------------------------------------
        self._order_repo.commit()
        self._fire_order_alerts(order, bot_id)

        return ServiceResult.ok(data=order)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _check_signal(self, signal_id: int, bot_id: int, side: str) -> ServiceResult[None]:
        signal = self._signal_repo.get_by_id(signal_id)
        if signal is None or signal.bot_id != bot_id:
            return ServiceResult.fail(code="SIGNAL_NOT_FOUND", http_status=404)

        if not signal.approved or signal.action != side:
            return ServiceResult.fail(
                code="ORDER_SIGNAL_MISMATCH",
                http_status=422,
                meta={"signal_action": signal.action, "approved": signal.approved},
            )

        if self._order_repo.has_active_order_for_signal(signal_id):
            return ServiceResult.fail(code="ORDER_SIGNAL_ALREADY_USED", http_status=409)

        return ServiceResult.ok(data=None)

    def _last_close(self, bot: Bot) -> Decimal | None:
        candles = self._candle_repo.list_candles(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            limit=1,
        )
        return candles[0].close if candles else None

    def _fire_order_alerts(self, order: Order, bot_id: int) -> None:
        """Hook de alertas (fire-and-forget — nunca bloquea la operación)."""
        if self._evaluate_alerts is None:
            return
        try:
            self._evaluate_alerts.evaluate_order_alerts(order=order, bot_id=bot_id)
        except Exception:
            pass
