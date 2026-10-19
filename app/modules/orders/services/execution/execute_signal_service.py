# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/execution/execute_signal_service.py
#
# PROPÓSITO:
# - Convertir una señal pendiente en orden: cuando la persona la aprueba
#   (app o Telegram) o cuando el agente está en modo automático.
# - Rechazar una señal pendiente.
#
# FLUJO DE EJECUCIÓN:
#   1. Señal del usuario (propiedad vía bot → cuenta), BUY/SELL aprobada
#   2. Si venció → `expired` (no se ejecuta tarde)
#   3. Reclamo atómico pending → executing (UPDATE condicional): si la app
#      y Telegram aprueban a la vez, solo uno gana
#   4. Revalidar al precio ACTUAL (puede haber pasado una hora):
#      - BUY: precio sobre el stop loss y R/R ≥ AGENT_MIN_RR_RATIO desde
#        el precio actual; no hay otra posición abierta (sin piramidar)
#      - SELL (spot): cierra la posición abierta; sin posición → falla
#   5. Cantidad: se recalcula para que el riesgo en dinero siga siendo el
#      de la señal (1 % del capital) con la distancia actual al SL
#   6. CreateOrderService (propiedad, RiskGate, idempotencia)
#   7. BUY ejecutada → la posición guarda SL/TP para el scheduler
#   8. executing → executed | failed (decision_reason = código)
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils.datetime_utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.services.orders.create_order_service import CreateOrderService


@dataclass
class SignalDecision:
    """Resultado de aprobar o rechazar: la señal actualizada y la orden, si hubo."""

    signal: Signal
    order: Order | None = None


class ExecuteSignalService:
    """Aprueba (ejecuta) o rechaza señales pendientes."""

    def __init__(
        self,
        signal_repo: SignalRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        candle_repo: CandleRepository,
        position_repo: PositionRepository,
        create_order: CreateOrderService,
        min_rr_ratio: float,
    ):
        self._signal_repo = signal_repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._candle_repo = candle_repo
        self._position_repo = position_repo
        self._create_order = create_order
        self._min_rr_ratio = Decimal(str(min_rr_ratio))

    # ==================================================================
    # Aprobar → ejecutar
    # ==================================================================

    def execute(
        self,
        signal_id: int,
        owner_id: int | None,
        decided_by_user_id: int | None,
        channel: str,
    ) -> ServiceResult[SignalDecision]:
        loaded = self._load_pending(signal_id, owner_id)
        if not loaded.success:
            return loaded  # type: ignore[return-value]
        signal, bot = loaded.data

        now = utc_now()
        claimed = self._signal_repo.transition_decision(
            signal_id,
            from_statuses=("pending",),
            to_status="executing",
            decided_at=now,
            decided_by_user_id=decided_by_user_id,
            decision_channel=channel,
        )
        self._signal_repo.commit()
        if not claimed:
            return ServiceResult.fail(code="SIGNAL_ALREADY_DECIDED", http_status=409)

        plan = self._plan_order(signal, bot)
        if not plan.success:
            return self._finish_failed(signal_id, plan.error.code, plan.error.http_status)
        side, qty = plan.data

        result = self._create_order.create(
            bot_id=bot.id,
            side=side,
            order_type="market",
            qty=qty,
            signal_id=signal.id,
            owner_id=owner_id,
            reason="signal",
        )
        if not result.success:
            return self._finish_failed(signal_id, result.error.code, result.error.http_status)

        order = result.data
        position = self._position_repo.get_by_bot_and_symbol(bot.id, bot.symbol_id)
        if side == "buy" and position is not None and not position.is_flat():
            position.set_protection(signal.stop_loss, signal.take_profit, signal.id)
            self._position_repo.update(position)

        self._signal_repo.transition_decision(
            signal_id, from_statuses=("executing",), to_status="executed"
        )
        self._signal_repo.commit()

        return ServiceResult.ok(
            data=SignalDecision(signal=self._signal_repo.get_by_id(signal_id), order=order)
        )

    # ==================================================================
    # Rechazar
    # ==================================================================

    def reject(
        self,
        signal_id: int,
        owner_id: int | None,
        decided_by_user_id: int | None,
        channel: str,
    ) -> ServiceResult[SignalDecision]:
        loaded = self._load_pending(signal_id, owner_id)
        if not loaded.success:
            return loaded  # type: ignore[return-value]

        rejected = self._signal_repo.transition_decision(
            signal_id,
            from_statuses=("pending",),
            to_status="rejected",
            decided_at=utc_now(),
            decided_by_user_id=decided_by_user_id,
            decision_channel=channel,
        )
        self._signal_repo.commit()
        if not rejected:
            return ServiceResult.fail(code="SIGNAL_ALREADY_DECIDED", http_status=409)

        return ServiceResult.ok(data=SignalDecision(signal=self._signal_repo.get_by_id(signal_id)))

    # ==================================================================
    # Helpers
    # ==================================================================

    def _load_pending(
        self, signal_id: int, owner_id: int | None
    ) -> ServiceResult[tuple[Signal, Bot]]:
        signal = self._signal_repo.get_by_id(signal_id)
        if signal is None:
            return ServiceResult.fail(code="SIGNAL_NOT_FOUND", http_status=404)

        bot = find_accessible_bot(self._bot_repo, self._account_repo, signal.bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="SIGNAL_NOT_FOUND", http_status=404)

        if not signal.is_actionable():
            return ServiceResult.fail(code="SIGNAL_NOT_ACTIONABLE", http_status=422)

        if not signal.is_pending():
            return ServiceResult.fail(
                code="SIGNAL_ALREADY_DECIDED",
                http_status=409,
                meta={"decision_status": signal.decision_status},
            )

        if signal.is_expired_at(utc_now()):
            self._signal_repo.transition_decision(
                signal_id, from_statuses=("pending",), to_status="expired"
            )
            self._signal_repo.commit()
            return ServiceResult.fail(code="SIGNAL_EXPIRED", http_status=409)

        return ServiceResult.ok(data=(signal, bot))

    def _plan_order(self, signal: Signal, bot: Bot) -> ServiceResult[tuple[str, Decimal]]:
        """Lado y cantidad de la orden, revalidados con el precio actual."""
        candles = self._candle_repo.list_candles(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            limit=1,
        )
        if not candles:
            return ServiceResult.fail(code="ORDER_NO_MARKET_PRICE", http_status=422)
        price = Decimal(str(candles[0].close))

        position = self._position_repo.get_by_bot_and_symbol(bot.id, bot.symbol_id)
        has_position = position is not None and not position.is_flat()

        if signal.action == "sell":
            # Spot: una venta solo cierra la posición abierta
            if not has_position:
                return ServiceResult.fail(code="SIGNAL_NO_POSITION", http_status=422)
            return ServiceResult.ok(data=("sell", position.qty))

        if has_position:
            return ServiceResult.fail(code="SIGNAL_POSITION_ALREADY_OPEN", http_status=409)

        stop_loss, take_profit = signal.stop_loss, signal.take_profit
        if stop_loss is None or take_profit is None or signal.position_size is None:
            return ServiceResult.fail(code="SIGNAL_NOT_ACTIONABLE", http_status=422)

        risk_now = price - stop_loss
        if risk_now <= Decimal("0") or price >= take_profit:
            return ServiceResult.fail(code="SIGNAL_PRICE_MOVED", http_status=409)
        if (take_profit - price) / risk_now < self._min_rr_ratio:
            return ServiceResult.fail(code="SIGNAL_PRICE_MOVED", http_status=409)

        # Mismo riesgo en dinero que calculó el agente (capital × risk_pct)
        risk_amount = signal.position_size * abs(signal.entry_price - stop_loss)
        qty = (risk_amount / risk_now).quantize(Decimal("0.000000000001"))
        if qty <= Decimal("0"):
            return ServiceResult.fail(code="ORDER_INVALID_QTY", http_status=422)

        return ServiceResult.ok(data=("buy", qty))

    def _finish_failed(
        self, signal_id: int, code: str, http_status: int
    ) -> ServiceResult[SignalDecision]:
        self._signal_repo.transition_decision(
            signal_id,
            from_statuses=("executing",),
            to_status="failed",
            decision_reason=code[:64],
        )
        self._signal_repo.commit()
        return ServiceResult.fail(code=code, http_status=http_status)
