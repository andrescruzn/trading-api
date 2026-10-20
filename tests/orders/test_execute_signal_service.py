# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_execute_signal_service.py
#
# Tests unitarios del ExecuteSignalService (aprobar / rechazar señales).
#
# ESTRATEGIA:
# - Repositorios y CreateOrderService son MagicMock.
# - `utc_now` se fija en el módulo del servicio para que el vencimiento
#   de la señal sea determinista.
# - Se verifican las reglas del flujo: propiedad, vencimiento, reclamo
#   atómico, revalidación al precio actual, recálculo de la cantidad
#   manteniendo el riesgo en dinero y el cierre de la decisión según lo
#   que devuelva CreateOrderService (que es quien aplica la protección).
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.services.execution import execute_signal_service as module
from app.modules.orders.services.execution.execute_signal_service import (
    ExecuteSignalService,
)

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
OWNER_ID = 7


# ======================================================================
# Helpers
# ======================================================================

@pytest.fixture(autouse=True)
def _fixed_now(monkeypatch):
    monkeypatch.setattr(module, "utc_now", lambda: NOW)


def _make_signal(
    action: str = "buy",
    approved: bool = True,
    decision_status: str = "pending",
    expires_at: datetime | None = NOW + timedelta(minutes=30),
    entry_price: Decimal | None = Decimal("100"),
    stop_loss: Decimal | None = Decimal("90"),
    take_profit: Decimal | None = Decimal("130"),
    position_size: Decimal | None = Decimal("1"),
) -> Signal:
    return Signal(
        id=11,
        bot_id=1,
        ts=NOW - timedelta(minutes=5),
        action=action,
        approved=approved,
        reasons={},
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size,
        decision_status=decision_status,
        expires_at=expires_at,
    )


def _make_bot(mode: str = "paper") -> Bot:
    return Bot(
        id=1,
        name="Agente de prueba",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode=mode,
        status="running",
        risk_params={"risk_pct": 0.01},
        execution_mode="approval",
    )


def _make_position(qty: Decimal = Decimal("1")) -> Position:
    return Position(id=40, bot_id=1, symbol_id=5, qty=qty, avg_price=Decimal("95"))


def _make_order(status: str = "filled") -> MagicMock:
    return MagicMock(id=500, status=status)


def _make_service(
    signal: Signal | None = None,
    bot: Bot | None = None,
    account_user_id: int = OWNER_ID,
    price: Decimal | None = Decimal("95"),
    position: Position | None = None,
    claimed: bool = True,
    order_result: ServiceResult | None = None,
):
    """Retorna (service, mocks) con un escenario BUY válido por defecto."""
    signal_repo = MagicMock()
    signal_repo.get_by_id.return_value = signal
    signal_repo.transition_decision.return_value = claimed

    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = MagicMock(user_id=account_user_id)

    candle_repo = MagicMock()
    candle_repo.list_candles.return_value = [] if price is None else [MagicMock(close=price)]

    position_repo = MagicMock()
    position_repo.get_by_bot_and_symbol.return_value = position

    create_order = MagicMock()
    create_order.create.return_value = order_result or ServiceResult.ok(data=_make_order())

    service = ExecuteSignalService(
        signal_repo=signal_repo,
        bot_repo=bot_repo,
        account_repo=account_repo,
        candle_repo=candle_repo,
        position_repo=position_repo,
        create_order=create_order,
        min_rr_ratio=2.0,
    )
    mocks = {
        "signal_repo": signal_repo,
        "position_repo": position_repo,
        "create_order": create_order,
        "candle_repo": candle_repo,
    }
    return service, mocks


def _execute(service: ExecuteSignalService, owner_id: int | None = OWNER_ID):
    return service.execute(signal_id=11, owner_id=owner_id, decided_by_user_id=OWNER_ID, channel="app")


def _transitions_to(signal_repo: MagicMock) -> list[str]:
    return [c.kwargs["to_status"] for c in signal_repo.transition_decision.call_args_list]


# ======================================================================
# TestLoadPending
# ======================================================================

class TestLoadPending:
    def test_missing_signal_returns_not_found(self):
        service, mocks = _make_service(signal=None, bot=_make_bot())

        result = _execute(service)

        assert result.success is False
        assert result.error.code == "SIGNAL_NOT_FOUND"
        assert result.error.http_status == 404
        mocks["create_order"].create.assert_not_called()

    def test_missing_bot_returns_not_found(self):
        service, _ = _make_service(signal=_make_signal(), bot=None)

        result = _execute(service)

        assert result.error.code == "SIGNAL_NOT_FOUND"

    def test_foreign_bot_returns_not_found(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), account_user_id=99)

        result = _execute(service, owner_id=OWNER_ID)

        assert result.success is False
        assert result.error.code == "SIGNAL_NOT_FOUND"
        assert result.error.http_status == 404
        mocks["signal_repo"].transition_decision.assert_not_called()

    def test_admin_without_owner_can_access_any_bot(self):
        service, _ = _make_service(signal=_make_signal(), bot=_make_bot(), account_user_id=99)

        result = _execute(service, owner_id=None)

        assert result.success is True

    def test_hold_signal_is_not_actionable(self):
        service, _ = _make_service(signal=_make_signal(action="hold"), bot=_make_bot())

        result = _execute(service)

        assert result.error.code == "SIGNAL_NOT_ACTIONABLE"
        assert result.error.http_status == 422

    def test_unapproved_signal_is_not_actionable(self):
        service, _ = _make_service(signal=_make_signal(approved=False), bot=_make_bot())

        result = _execute(service)

        assert result.error.code == "SIGNAL_NOT_ACTIONABLE"

    def test_already_expired_signal_returns_expired(self):
        service, mocks = _make_service(
            signal=_make_signal(decision_status="expired"), bot=_make_bot()
        )

        result = _execute(service)

        assert result.error.code == "SIGNAL_EXPIRED"
        assert result.error.http_status == 409
        mocks["signal_repo"].transition_decision.assert_not_called()

    def test_pending_signal_expired_at_now_transitions_to_expired(self):
        service, mocks = _make_service(signal=_make_signal(expires_at=NOW), bot=_make_bot())

        result = _execute(service)

        assert result.error.code == "SIGNAL_EXPIRED"
        assert result.error.http_status == 409
        mocks["signal_repo"].transition_decision.assert_called_once_with(
            11, from_statuses=("pending",), to_status="expired"
        )
        mocks["signal_repo"].commit.assert_called_once()
        mocks["create_order"].create.assert_not_called()

    def test_not_pending_signal_returns_already_decided(self):
        service, mocks = _make_service(
            signal=_make_signal(decision_status="executed"), bot=_make_bot()
        )

        result = _execute(service)

        assert result.error.code == "SIGNAL_ALREADY_DECIDED"
        assert result.error.http_status == 409
        assert result.error.meta == {"decision_status": "executed"}
        mocks["signal_repo"].transition_decision.assert_not_called()


# ======================================================================
# TestAtomicClaim
# ======================================================================

class TestAtomicClaim:
    def test_claims_pending_to_executing_with_decision_data(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot())

        _execute(service)

        first = mocks["signal_repo"].transition_decision.call_args_list[0]
        assert first.args == (11,)
        assert first.kwargs == {
            "from_statuses": ("pending",),
            "to_status": "executing",
            "decided_at": NOW,
            "decided_by_user_id": OWNER_ID,
            "decision_channel": "app",
        }

    def test_losing_the_claim_returns_already_decided_without_order(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), claimed=False)

        result = _execute(service)

        assert result.success is False
        assert result.error.code == "SIGNAL_ALREADY_DECIDED"
        assert result.error.http_status == 409
        mocks["create_order"].create.assert_not_called()
        assert _transitions_to(mocks["signal_repo"]) == ["executing"]


# ======================================================================
# TestPlanOrder
# ======================================================================

class TestPlanOrder:
    def test_sell_without_position_fails_with_no_position(self):
        service, mocks = _make_service(
            signal=_make_signal(action="sell"), bot=_make_bot(), position=None
        )

        result = _execute(service)

        assert result.error.code == "SIGNAL_NO_POSITION"
        assert result.error.http_status == 422
        mocks["create_order"].create.assert_not_called()

    def test_sell_with_flat_position_fails_with_no_position(self):
        service, _ = _make_service(
            signal=_make_signal(action="sell"),
            bot=_make_bot(),
            position=_make_position(Decimal("0")),
        )

        result = _execute(service)

        assert result.error.code == "SIGNAL_NO_POSITION"

    def test_sell_with_position_sells_the_whole_position(self):
        service, mocks = _make_service(
            signal=_make_signal(action="sell"),
            bot=_make_bot(),
            position=_make_position(Decimal("1.5")),
        )

        result = _execute(service)

        assert result.success is True
        kwargs = mocks["create_order"].create.call_args.kwargs
        assert kwargs["side"] == "sell"
        assert kwargs["qty"] == Decimal("1.5")
        assert kwargs["reason"] == "signal"

    def test_buy_with_open_position_fails_without_pyramiding(self):
        service, mocks = _make_service(
            signal=_make_signal(), bot=_make_bot(), position=_make_position()
        )

        result = _execute(service)

        assert result.error.code == "SIGNAL_POSITION_ALREADY_OPEN"
        assert result.error.http_status == 409
        mocks["create_order"].create.assert_not_called()

    def test_buy_with_flat_position_is_allowed(self):
        service, _ = _make_service(
            signal=_make_signal(), bot=_make_bot(), position=_make_position(Decimal("0"))
        )

        result = _execute(service)

        assert result.success is True

    def test_without_market_price_fails(self):
        service, _ = _make_service(signal=_make_signal(), bot=_make_bot(), price=None)

        result = _execute(service)

        assert result.error.code == "ORDER_NO_MARKET_PRICE"

    @pytest.mark.parametrize("price", [Decimal("90"), Decimal("85")])
    def test_price_at_or_below_stop_loss_fails_with_price_moved(self, price):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), price=price)

        result = _execute(service)

        assert result.error.code == "SIGNAL_PRICE_MOVED"
        assert result.error.http_status == 409
        mocks["create_order"].create.assert_not_called()

    @pytest.mark.parametrize("price", [Decimal("130"), Decimal("135")])
    def test_price_at_or_above_take_profit_fails_with_price_moved(self, price):
        service, _ = _make_service(signal=_make_signal(), bot=_make_bot(), price=price)

        result = _execute(service)

        assert result.error.code == "SIGNAL_PRICE_MOVED"

    def test_rr_below_min_from_current_price_fails_with_price_moved(self):
        # Precio 110: riesgo 20, beneficio 20 → R/R 1 < 2
        service, _ = _make_service(signal=_make_signal(), bot=_make_bot(), price=Decimal("110"))

        result = _execute(service)

        assert result.error.code == "SIGNAL_PRICE_MOVED"

    def test_rr_exactly_min_from_current_price_is_accepted(self):
        # Precio 110 con TP 150: riesgo 20, beneficio 40 → R/R 2
        service, _ = _make_service(
            signal=_make_signal(take_profit=Decimal("150")), bot=_make_bot(), price=Decimal("110")
        )

        result = _execute(service)

        assert result.success is True

    def test_buy_without_position_size_is_not_actionable(self):
        service, _ = _make_service(signal=_make_signal(position_size=None), bot=_make_bot())

        result = _execute(service)

        assert result.error.code == "SIGNAL_NOT_ACTIONABLE"

    def test_plan_failure_marks_signal_failed_with_code(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), price=Decimal("85"))

        _execute(service)

        last = mocks["signal_repo"].transition_decision.call_args_list[-1]
        assert last.kwargs == {
            "from_statuses": ("executing",),
            "to_status": "failed",
            "decision_reason": "SIGNAL_PRICE_MOVED",
        }


# ======================================================================
# TestQuantityRecalculation
# ======================================================================

class TestQuantityRecalculation:
    def test_qty_keeps_money_at_risk_with_current_stop_distance(self):
        # position_size 1, entrada 100, SL 90 → riesgo 10; precio 95 → qty = 10 / 5 = 2
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), price=Decimal("95"))

        result = _execute(service)

        assert result.success is True
        kwargs = mocks["create_order"].create.call_args.kwargs
        assert kwargs["side"] == "buy"
        assert kwargs["order_type"] == "market"
        assert kwargs["qty"] == Decimal("2")
        assert kwargs["signal_id"] == 11
        assert kwargs["owner_id"] == OWNER_ID
        assert kwargs["reason"] == "signal"

    def test_qty_shrinks_when_price_moved_away_from_stop(self):
        # riesgo 10; precio 100.5 → distancia 10.5 → qty = 0.952380952381 (12 decimales)
        service, mocks = _make_service(
            signal=_make_signal(take_profit=Decimal("150")), bot=_make_bot(), price=Decimal("100.5")
        )

        _execute(service)

        qty = mocks["create_order"].create.call_args.kwargs["qty"]
        assert qty == Decimal("0.952380952381")


# ======================================================================
# TestProtectionDelegation
# ======================================================================

class TestProtectionDelegation:
    """La protección la aplica CreateOrderService: el servicio solo la pasa."""

    def test_buy_passes_signal_stop_loss_and_take_profit_to_create(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(mode="live"))

        _execute(service)

        kwargs = mocks["create_order"].create.call_args.kwargs
        assert kwargs["stop_loss"] == Decimal("90")
        assert kwargs["take_profit"] == Decimal("130")

    def test_sell_passes_no_protection_to_create(self):
        service, mocks = _make_service(
            signal=_make_signal(action="sell"),
            bot=_make_bot(mode="live"),
            position=_make_position(Decimal("1")),
        )

        _execute(service)

        kwargs = mocks["create_order"].create.call_args.kwargs
        assert kwargs["stop_loss"] is None
        assert kwargs["take_profit"] is None

    def test_service_does_not_touch_the_position(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(mode="live"))

        _execute(service)

        mocks["position_repo"].update.assert_not_called()
        mocks["position_repo"].commit.assert_not_called()


# ======================================================================
# TestDecisionOutcome
# ======================================================================

class TestDecisionOutcome:
    @pytest.mark.parametrize("status", ["filled", "partially_filled"])
    def test_executed_order_marks_signal_executed(self, status):
        signal = _make_signal()
        order = _make_order(status=status)
        service, mocks = _make_service(
            signal=signal, bot=_make_bot(), order_result=ServiceResult.ok(data=order)
        )

        result = _execute(service)

        assert result.success is True
        assert result.data.signal is signal
        assert result.data.order is order
        assert _transitions_to(mocks["signal_repo"]) == ["executing", "executed"]
        executed = mocks["signal_repo"].transition_decision.call_args_list[-1]
        assert executed.kwargs == {"from_statuses": ("executing",), "to_status": "executed"}
        assert mocks["signal_repo"].commit.call_count == 2

    def test_sent_order_keeps_signal_executing_and_returns_ok(self):
        signal = _make_signal()
        order = _make_order(status="sent")
        service, mocks = _make_service(
            signal=signal, bot=_make_bot(mode="live"), order_result=ServiceResult.ok(data=order)
        )

        result = _execute(service)

        assert result.success is True
        assert result.data.signal is signal
        assert result.data.order is order
        assert _transitions_to(mocks["signal_repo"]) == ["executing"]

    def test_uncertain_execution_keeps_signal_executing_and_returns_same_error(self):
        service, mocks = _make_service(
            signal=_make_signal(),
            bot=_make_bot(mode="live"),
            order_result=ServiceResult.fail(
                code="ORDER_EXECUTION_UNCERTAIN", http_status=502, meta={"order_id": 500}
            ),
        )

        result = _execute(service)

        assert result.success is False
        assert result.error.code == "ORDER_EXECUTION_UNCERTAIN"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": 500}
        assert _transitions_to(mocks["signal_repo"]) == ["executing"]

    def test_create_order_failure_marks_signal_failed_with_code(self):
        service, mocks = _make_service(
            signal=_make_signal(),
            bot=_make_bot(),
            order_result=ServiceResult.fail(code="RISK_DAILY_LOSS_LIMIT", http_status=409),
        )

        result = _execute(service)

        assert result.success is False
        assert result.error.code == "RISK_DAILY_LOSS_LIMIT"
        assert result.error.http_status == 409
        last = mocks["signal_repo"].transition_decision.call_args_list[-1]
        assert last.kwargs == {
            "from_statuses": ("executing",),
            "to_status": "failed",
            "decision_reason": "RISK_DAILY_LOSS_LIMIT",
        }
        assert "executed" not in _transitions_to(mocks["signal_repo"])

    def test_execution_failed_marks_signal_failed(self):
        service, mocks = _make_service(
            signal=_make_signal(),
            bot=_make_bot(mode="live"),
            order_result=ServiceResult.fail(code="ORDER_EXECUTION_FAILED", http_status=502),
        )

        _execute(service)

        assert _transitions_to(mocks["signal_repo"]) == ["executing", "failed"]

    def test_failed_reason_is_truncated_to_64_chars(self):
        service, mocks = _make_service(
            signal=_make_signal(),
            bot=_make_bot(),
            order_result=ServiceResult.fail(code="X" * 80, http_status=422),
        )

        _execute(service)

        last = mocks["signal_repo"].transition_decision.call_args_list[-1]
        assert last.kwargs["decision_reason"] == "X" * 64


# ======================================================================
# TestReject
# ======================================================================

class TestReject:
    def test_reject_transitions_pending_to_rejected(self):
        signal = _make_signal()
        service, mocks = _make_service(signal=signal, bot=_make_bot())

        result = service.reject(
            signal_id=11, owner_id=OWNER_ID, decided_by_user_id=OWNER_ID, channel="telegram"
        )

        assert result.success is True
        assert result.data.signal is signal
        assert result.data.order is None
        mocks["signal_repo"].transition_decision.assert_called_once_with(
            11,
            from_statuses=("pending",),
            to_status="rejected",
            decided_at=NOW,
            decided_by_user_id=OWNER_ID,
            decision_channel="telegram",
        )
        mocks["signal_repo"].commit.assert_called_once()
        mocks["create_order"].create.assert_not_called()

    def test_reject_losing_the_claim_returns_already_decided(self):
        service, _ = _make_service(signal=_make_signal(), bot=_make_bot(), claimed=False)

        result = service.reject(
            signal_id=11, owner_id=OWNER_ID, decided_by_user_id=OWNER_ID, channel="app"
        )

        assert result.error.code == "SIGNAL_ALREADY_DECIDED"
        assert result.error.http_status == 409

    def test_reject_expired_signal_returns_expired(self):
        service, mocks = _make_service(signal=_make_signal(expires_at=NOW), bot=_make_bot())

        result = service.reject(
            signal_id=11, owner_id=OWNER_ID, decided_by_user_id=OWNER_ID, channel="app"
        )

        assert result.error.code == "SIGNAL_EXPIRED"
        assert _transitions_to(mocks["signal_repo"]) == ["expired"]

    def test_reject_foreign_signal_returns_not_found(self):
        service, mocks = _make_service(signal=_make_signal(), bot=_make_bot(), account_user_id=99)

        result = service.reject(
            signal_id=11, owner_id=OWNER_ID, decided_by_user_id=OWNER_ID, channel="app"
        )

        assert result.error.code == "SIGNAL_NOT_FOUND"
        mocks["signal_repo"].transition_decision.assert_not_called()
