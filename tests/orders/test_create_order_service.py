# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_create_order_service.py
#
# Tests unitarios del CreateOrderService (lógica central del Módulo 8).
#
# ESTRATEGIA:
# - Todos los repositorios, el RiskGate, los executors, el hook de
#   alertas y el NativeStopService son MagicMock (sin BD ni red).
# - Bot y Position son entidades reales: así se prueba el efecto real
#   de apply_fill y de set_protection sobre la posición.
# - El bot se busca con owner_id=None (admin) para no depender de la
#   regla de propiedad; esa regla se prueba en un caso aparte.
# - Para comprobar "persistir antes de enviar" los mocks cuelgan de un
#   padre común y se compara el orden de `mock_calls`.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.execution.executor_interface import (
    ExecutionResult,
    ExecutionUncertainError,
)
from app.modules.orders.services.orders.create_order_service import CreateOrderService

_ORDER_ID = 42
_LAST_CLOSE = Decimal("100")


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(status: str = "running", mode: str = "paper") -> Bot:
    return Bot(
        id=1,
        name="Agente de prueba",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode=mode,
        status=status,
        risk_params={"risk_pct": 0.01},
    )


def _make_position(qty: str = "1", sl_order_id: int | None = None) -> Position:
    return Position(
        id=7,
        bot_id=1,
        symbol_id=5,
        qty=Decimal(qty),
        avg_price=Decimal("90"),
        sl_order_id=sl_order_id,
    )


def _make_fill(qty: str = "1", price: Decimal = _LAST_CLOSE) -> Fill:
    return Fill(
        id=0,
        order_id=0,
        qty=Decimal(qty),
        price=price,
        exchange_trade_id="paper-trade-1",
    )


def _make_signal(bot_id: int = 1, action: str = "buy", approved: int = 1):
    return SimpleNamespace(id=55, bot_id=bot_id, action=action, approved=approved)


def _make_service(
    bot: Bot | None = None,
    position: Position | None = None,
    candles: list | None = None,
    gate: ServiceResult | None = None,
    exec_result: ExecutionResult | None = None,
    exec_error: Exception | None = None,
    signal=None,
    signal_used: bool = False,
    native_cancel: ServiceResult | None = None,
    place_native_stop: bool = False,
):
    """Retorna (service, mocks). Todos los mocks cuelgan de `mocks.parent`."""
    parent = MagicMock()

    order_repo = parent.order_repo
    created_orders: list = []

    def _create_order(order):
        order.id = _ORDER_ID
        created_orders.append(order)
        return order

    order_repo.create.side_effect = _create_order
    order_repo.update.side_effect = lambda o: o
    order_repo.has_active_order_for_signal.return_value = signal_used

    fill_repo = parent.fill_repo
    fill_repo.create.side_effect = lambda f: f

    position_repo = parent.position_repo
    position_repo.get_by_bot_and_symbol.return_value = position
    position_repo.create.side_effect = lambda p: p
    position_repo.update.side_effect = lambda p: p

    bot_repo = parent.bot_repo
    bot_repo.get_by_id.return_value = bot

    signal_repo = parent.signal_repo
    signal_repo.get_by_id.return_value = signal

    symbol_repo = parent.symbol_repo
    symbol_repo.get_by_id.return_value = SimpleNamespace(id=5, symbol="BTC/USDT")

    candle_repo = parent.candle_repo
    candle_repo.list_candles.return_value = (
        [SimpleNamespace(close=_LAST_CLOSE)] if candles is None else candles
    )

    risk_gate = parent.risk_gate
    risk_gate.check.return_value = gate or ServiceResult.ok(data=None)

    default_result = exec_result or ExecutionResult(status="filled", fill=_make_fill())
    paper = parent.paper
    live = parent.live
    for executor in (paper, live):
        if exec_error is not None:
            executor.execute.side_effect = exec_error
        else:
            executor.execute.return_value = default_result

    native_stop = parent.native_stop
    native_stop.cancel.return_value = native_cancel or ServiceResult.ok(data=None)

    evaluate_alerts = parent.evaluate_alerts

    service = CreateOrderService(
        order_repo=order_repo,
        fill_repo=fill_repo,
        position_repo=position_repo,
        bot_repo=bot_repo,
        account_repo=parent.account_repo,
        signal_repo=signal_repo,
        symbol_repo=symbol_repo,
        candle_repo=candle_repo,
        risk_gate=risk_gate,
        paper_executor=paper,
        live_executor=live,
        evaluate_alerts=evaluate_alerts,
        native_stop=native_stop,
        place_native_stop=place_native_stop,
        min_rr_ratio=Decimal("2"),
    )
    mocks = SimpleNamespace(
        parent=parent,
        order_repo=order_repo,
        fill_repo=fill_repo,
        position_repo=position_repo,
        account_repo=parent.account_repo,
        risk_gate=risk_gate,
        paper=paper,
        live=live,
        native_stop=native_stop,
        evaluate_alerts=evaluate_alerts,
        created_orders=created_orders,
    )
    return service, mocks


def _buy(service: CreateOrderService, **overrides):
    kwargs = {"bot_id": 1, "side": "buy", "order_type": "market", "qty": Decimal("1")}
    kwargs.update(overrides)
    return service.create(**kwargs)


def _assert_nothing_created(mocks) -> None:
    mocks.order_repo.create.assert_not_called()
    mocks.order_repo.commit.assert_not_called()
    mocks.paper.execute.assert_not_called()
    mocks.live.execute.assert_not_called()


# ======================================================================
# TestBotValidation
# ======================================================================

class TestBotValidation:
    def test_missing_bot_returns_bot_not_found(self):
        service, mocks = _make_service(bot=None)

        result = _buy(service)

        assert result.success is False
        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
        _assert_nothing_created(mocks)

    def test_foreign_bot_returns_bot_not_found(self):
        service, mocks = _make_service(bot=_make_bot())
        mocks.account_repo.get_by_id.return_value = SimpleNamespace(id=2, user_id=99)

        result = _buy(service, owner_id=7)

        assert result.success is False
        assert result.error.code == "BOT_NOT_FOUND"
        _assert_nothing_created(mocks)

    @pytest.mark.parametrize("status", ["stopped", "paused", "error"])
    def test_bot_not_running_returns_409(self, status):
        service, mocks = _make_service(bot=_make_bot(status=status))

        result = _buy(service)

        assert result.success is False
        assert result.error.code == "BOT_NOT_RUNNING"
        assert result.error.http_status == 409
        assert result.error.meta == {"status": status}
        _assert_nothing_created(mocks)

    def test_bot_not_running_is_allowed_when_require_running_is_false(self):
        position = _make_position(qty="1")
        service, mocks = _make_service(bot=_make_bot(status="paused"), position=position)

        result = service.create(
            bot_id=1,
            side="sell",
            order_type="market",
            qty=Decimal("1"),
            require_running=False,
            reason="stop_loss",
        )

        assert result.success is True
        assert result.data.meta["reason"] == "stop_loss"
        mocks.paper.execute.assert_called_once()


# ======================================================================
# TestOrderParamsValidation
# ======================================================================

class TestOrderParamsValidation:
    @pytest.mark.parametrize("side", ["hold", "BUY", ""])
    def test_invalid_side_returns_422(self, side):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, side=side)

        assert result.error.code == "ORDER_INVALID_SIDE"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_invalid_type_returns_422(self):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, order_type="trailing")

        assert result.error.code == "ORDER_INVALID_TYPE"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    @pytest.mark.parametrize("qty", ["0", "-1"])
    def test_non_positive_qty_returns_422(self, qty):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, qty=Decimal(qty))

        assert result.error.code == "ORDER_INVALID_QTY"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    @pytest.mark.parametrize("order_type", ["limit", "stop_limit"])
    @pytest.mark.parametrize("price", [None, Decimal("0")])
    def test_limit_without_price_returns_price_required(self, order_type, price):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, order_type=order_type, price=price, stop_price=Decimal("99"))

        assert result.error.code == "ORDER_PRICE_REQUIRED"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_stop_without_stop_price_returns_stop_price_required(self):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, order_type="stop")

        assert result.error.code == "ORDER_STOP_PRICE_REQUIRED"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_stop_limit_with_price_but_no_stop_price_returns_stop_price_required(self):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, order_type="stop_limit", price=Decimal("101"))

        assert result.error.code == "ORDER_STOP_PRICE_REQUIRED"
        _assert_nothing_created(mocks)


# ======================================================================
# TestSignalChecks
# ======================================================================

class TestSignalChecks:
    def test_missing_signal_returns_signal_not_found(self):
        service, mocks = _make_service(bot=_make_bot(), signal=None)

        result = _buy(service, signal_id=55)

        assert result.error.code == "SIGNAL_NOT_FOUND"
        assert result.error.http_status == 404
        _assert_nothing_created(mocks)

    def test_signal_of_another_bot_returns_signal_not_found(self):
        service, mocks = _make_service(bot=_make_bot(), signal=_make_signal(bot_id=999))

        result = _buy(service, signal_id=55)

        assert result.error.code == "SIGNAL_NOT_FOUND"
        _assert_nothing_created(mocks)

    def test_unapproved_signal_returns_mismatch(self):
        service, mocks = _make_service(bot=_make_bot(), signal=_make_signal(approved=0))

        result = _buy(service, signal_id=55)

        assert result.error.code == "ORDER_SIGNAL_MISMATCH"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_signal_with_opposite_direction_returns_mismatch(self):
        service, mocks = _make_service(bot=_make_bot(), signal=_make_signal(action="sell"))

        result = _buy(service, signal_id=55)

        assert result.error.code == "ORDER_SIGNAL_MISMATCH"
        _assert_nothing_created(mocks)

    def test_signal_with_active_order_returns_already_used(self):
        service, mocks = _make_service(
            bot=_make_bot(), signal=_make_signal(), signal_used=True
        )

        result = _buy(service, signal_id=55)

        assert result.error.code == "ORDER_SIGNAL_ALREADY_USED"
        assert result.error.http_status == 409
        _assert_nothing_created(mocks)

    def test_valid_signal_links_order_and_sets_reason_signal(self):
        service, _ = _make_service(bot=_make_bot(), signal=_make_signal())

        result = _buy(service, signal_id=55)

        assert result.success is True
        assert result.data.signal_id == 55
        assert result.data.meta["reason"] == "signal"


# ======================================================================
# TestMarketPriceAndSpotRules
# ======================================================================

class TestMarketPriceAndSpotRules:
    def test_market_order_without_candles_returns_no_market_price(self):
        service, mocks = _make_service(bot=_make_bot(), candles=[])

        result = _buy(service)

        assert result.error.code == "ORDER_NO_MARKET_PRICE"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_limit_order_uses_its_price_as_reference_without_candles(self):
        service, mocks = _make_service(
            bot=_make_bot(),
            candles=[],
            exec_result=ExecutionResult(status="sent", exchange_order_id="ex-1"),
        )

        result = _buy(service, order_type="limit", price=Decimal("95"))

        assert result.success is True
        mocks.risk_gate.check.assert_called_once()
        assert mocks.risk_gate.check.call_args.kwargs["reference_price"] == Decimal("95")

    def test_sell_without_position_returns_exceeds_position(self):
        service, mocks = _make_service(bot=_make_bot(), position=None)

        result = _buy(service, side="sell")

        assert result.error.code == "ORDER_SELL_EXCEEDS_POSITION"
        assert result.error.http_status == 422
        assert result.error.meta == {"held": "0"}
        _assert_nothing_created(mocks)

    def test_sell_more_than_held_returns_exceeds_position(self):
        service, mocks = _make_service(bot=_make_bot(), position=_make_position(qty="0.5"))

        result = _buy(service, side="sell", qty=Decimal("0.6"))

        assert result.error.code == "ORDER_SELL_EXCEEDS_POSITION"
        assert result.error.meta == {"held": "0.5"}
        _assert_nothing_created(mocks)

    def test_sell_exactly_the_held_qty_is_allowed(self):
        position = _make_position(qty="0.5")
        service, _ = _make_service(
            bot=_make_bot(),
            position=position,
            exec_result=ExecutionResult(status="filled", fill=_make_fill(qty="0.5")),
        )

        result = _buy(service, side="sell", qty=Decimal("0.5"))

        assert result.success is True
        assert position.is_flat()


# ======================================================================
# TestRiskGate
# ======================================================================

class TestRiskGate:
    def test_risk_gate_failure_is_propagated_and_nothing_is_created(self):
        gate = ServiceResult.fail(
            code="ORDER_MAX_NOTIONAL_EXCEEDED", http_status=422, meta={"max": "1000"}
        )
        service, mocks = _make_service(bot=_make_bot(), gate=gate)

        result = _buy(service)

        assert result.success is False
        assert result.error.code == "ORDER_MAX_NOTIONAL_EXCEEDED"
        assert result.error.http_status == 422
        assert result.error.meta == {"max": "1000"}
        _assert_nothing_created(mocks)
        mocks.fill_repo.create.assert_not_called()

    def test_risk_gate_receives_bot_side_qty_and_last_close(self):
        bot = _make_bot()
        service, mocks = _make_service(bot=bot)

        _buy(service, qty=Decimal("2"))

        mocks.risk_gate.check.assert_called_once_with(
            bot=bot, side="buy", qty=Decimal("2"), reference_price=_LAST_CLOSE
        )


# ======================================================================
# TestPersistBeforeSend
# ======================================================================

class TestPersistBeforeSend:
    def test_order_is_created_as_new_with_meta(self):
        service, mocks = _make_service(bot=_make_bot())

        _buy(service)

        created = mocks.order_repo.create.call_args.args[0]
        assert created.bot_id == 1
        assert created.side == "buy"
        assert created.type == "market"
        assert created.qty == Decimal("1")
        assert created.meta["symbol"] == "BTC/USDT"
        assert created.meta["mode"] == "paper"
        assert created.meta["reason"] == "manual"
        assert created.ts is not None

    def test_status_is_new_when_commit_happens_before_execute(self):
        statuses_at_commit: list[str] = []
        service, mocks = _make_service(bot=_make_bot())
        mocks.order_repo.commit.side_effect = lambda: statuses_at_commit.append(
            mocks.created_orders[0].status
        )

        _buy(service)

        assert statuses_at_commit[0] == "new"

    def test_client_order_id_is_ta_prefixed_order_id(self):
        service, _ = _make_service(bot=_make_bot())

        result = _buy(service)

        assert result.data.client_order_id == f"ta-{_ORDER_ID}"

    def test_commit_happens_before_executor_execute(self):
        service, mocks = _make_service(bot=_make_bot())

        _buy(service)

        calls = mocks.parent.mock_calls
        first_commit = calls.index(call.order_repo.commit())
        execute_idx = next(i for i, c in enumerate(calls) if c[0] == "paper.execute")
        create_idx = next(i for i, c in enumerate(calls) if c[0] == "order_repo.create")
        assert create_idx < first_commit < execute_idx

    def test_order_sent_to_executor_already_has_client_order_id(self):
        service, mocks = _make_service(bot=_make_bot())

        _buy(service)

        sent_order = mocks.paper.execute.call_args.args[0]
        assert sent_order.client_order_id == f"ta-{_ORDER_ID}"


# ======================================================================
# TestExecutionResult
# ======================================================================

class TestExecutionResult:
    def test_paper_bot_uses_paper_executor(self):
        service, mocks = _make_service(bot=_make_bot(mode="paper"))

        _buy(service)

        mocks.paper.execute.assert_called_once()
        mocks.live.execute.assert_not_called()

    def test_live_bot_uses_live_executor(self):
        service, mocks = _make_service(bot=_make_bot(mode="live"))

        _buy(service)

        mocks.live.execute.assert_called_once()
        mocks.paper.execute.assert_not_called()

    def test_paper_filled_creates_fill_and_new_position(self):
        service, mocks = _make_service(
            bot=_make_bot(),
            position=None,
            exec_result=ExecutionResult(status="filled", fill=_make_fill(qty="2")),
        )

        result = _buy(service, qty=Decimal("2"))

        assert result.success is True
        assert result.data.status == "filled"
        fill = mocks.fill_repo.create.call_args.args[0]
        assert fill.order_id == _ORDER_ID
        new_position = mocks.position_repo.create.call_args.args[0]
        assert new_position.qty == Decimal("2")
        assert new_position.avg_price == _LAST_CLOSE
        assert mocks.order_repo.commit.call_count == 2

    def test_fill_trade_id_is_used_when_no_exchange_order_id(self):
        service, _ = _make_service(bot=_make_bot())

        result = _buy(service)

        assert result.data.exchange_order_id == "paper-trade-1"

    def test_buy_fill_updates_existing_position_with_wap(self):
        position = _make_position(qty="1")  # 1 @ 90
        service, mocks = _make_service(bot=_make_bot(), position=position)

        _buy(service)  # 1 @ 100

        mocks.position_repo.update.assert_called_with(position)
        assert position.qty == Decimal("2")
        assert position.avg_price == Decimal("95")

    def test_sell_fill_reduces_position_and_accumulates_pnl(self):
        position = _make_position(qty="2")  # 2 @ 90
        service, _ = _make_service(bot=_make_bot(), position=position)

        _buy(service, side="sell", qty=Decimal("1"))  # 1 @ 100

        assert position.qty == Decimal("1")
        assert position.realized_pnl == Decimal("10")

    def test_live_sent_without_fill_does_not_create_fill_or_touch_position(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"),
            exec_result=ExecutionResult(status="sent", exchange_order_id="ex-9"),
        )

        result = _buy(service, order_type="limit", price=Decimal("95"))

        assert result.success is True
        assert result.data.status == "sent"
        assert result.data.exchange_order_id == "ex-9"
        mocks.fill_repo.create.assert_not_called()
        mocks.position_repo.create.assert_not_called()
        mocks.position_repo.update.assert_not_called()

    def test_success_fires_order_alerts(self):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service)

        mocks.evaluate_alerts.evaluate_order_alerts.assert_called_once_with(
            order=result.data, bot_id=1
        )

    def test_alert_failure_does_not_break_the_order(self):
        service, mocks = _make_service(bot=_make_bot())
        mocks.evaluate_alerts.evaluate_order_alerts.side_effect = Exception("boom")

        result = _buy(service)

        assert result.success is True


# ======================================================================
# TestExecutionErrors
# ======================================================================

class TestExecutionErrors:
    def test_uncertain_error_leaves_order_sent_with_needs_reconciliation(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"), exec_error=ExecutionUncertainError("timeout")
        )

        result = _buy(service)

        assert result.success is False
        assert result.error.code == "ORDER_EXECUTION_UNCERTAIN"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": _ORDER_ID}
        order = mocks.created_orders[0]
        assert order.status == "sent"
        assert order.meta["needs_reconciliation"] is True
        assert order.meta["error"] == "timeout"
        assert mocks.order_repo.commit.call_count == 2
        mocks.order_repo.rollback.assert_not_called()
        mocks.fill_repo.create.assert_not_called()

    def test_runtime_error_marks_order_rejected_and_fires_alert(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"), exec_error=RuntimeError("insufficient balance")
        )

        result = _buy(service)

        assert result.success is False
        assert result.error.code == "ORDER_EXECUTION_FAILED"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": _ORDER_ID}
        order = mocks.created_orders[0]
        assert order.status == "rejected"
        assert order.meta["error"] == "insufficient balance"
        assert "needs_reconciliation" not in order.meta
        assert mocks.order_repo.commit.call_count == 2
        mocks.order_repo.rollback.assert_not_called()
        mocks.evaluate_alerts.evaluate_order_alerts.assert_called_once_with(
            order=order, bot_id=1
        )
        mocks.fill_repo.create.assert_not_called()


# ======================================================================
# TestNativeStopOnSell
# ======================================================================

class TestNativeStopOnSell:
    def test_sell_of_position_with_native_stop_cancels_it_before_order(self):
        bot = _make_bot(mode="live")
        position = _make_position(qty="1", sl_order_id=77)
        service, mocks = _make_service(bot=bot, position=position)

        result = _buy(service, side="sell")

        assert result.success is True
        mocks.native_stop.cancel.assert_called_once_with(bot, position)
        calls = mocks.parent.mock_calls
        cancel_idx = next(i for i, c in enumerate(calls) if c[0] == "native_stop.cancel")
        create_idx = next(i for i, c in enumerate(calls) if c[0] == "order_repo.create")
        assert cancel_idx < create_idx

    def test_native_stop_cancel_failure_blocks_sell(self):
        position = _make_position(qty="1", sl_order_id=77)
        service, mocks = _make_service(
            bot=_make_bot(mode="live"),
            position=position,
            native_cancel=ServiceResult.fail(code="ORDER_NATIVE_STOP_ACTIVE", http_status=409),
        )

        result = _buy(service, side="sell")

        assert result.success is False
        assert result.error.code == "ORDER_NATIVE_STOP_ACTIVE"
        assert result.error.http_status == 409
        _assert_nothing_created(mocks)

    def test_sell_without_native_stop_does_not_cancel(self):
        service, mocks = _make_service(bot=_make_bot(mode="live"), position=_make_position())

        _buy(service, side="sell")

        mocks.native_stop.cancel.assert_not_called()

    def test_buy_on_position_with_native_stop_does_not_cancel(self):
        position = _make_position(qty="1", sl_order_id=77)
        service, mocks = _make_service(bot=_make_bot(mode="live"), position=position)

        _buy(service)

        mocks.native_stop.cancel.assert_not_called()


# ======================================================================
# TestManualProtectionValidation
# ======================================================================

class TestManualProtectionValidation:
    def test_protection_on_sell_returns_market_buy_only(self):
        service, mocks = _make_service(bot=_make_bot(), position=_make_position())

        result = _buy(service, side="sell", stop_loss=Decimal("95"))

        assert result.error.code == "ORDER_PROTECTION_MARKET_BUY_ONLY"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_protection_on_limit_buy_returns_market_buy_only(self):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(
            service, order_type="limit", price=Decimal("99"), take_profit=Decimal("120")
        )

        assert result.error.code == "ORDER_PROTECTION_MARKET_BUY_ONLY"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    @pytest.mark.parametrize("stop_loss", ["100", "101"])
    def test_stop_loss_at_or_above_price_is_invalid(self, stop_loss):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, stop_loss=Decimal(stop_loss))

        assert result.error.code == "ORDER_INVALID_STOP_LOSS"
        assert result.error.http_status == 422
        assert result.error.meta == {"price": "100"}
        _assert_nothing_created(mocks)

    @pytest.mark.parametrize("take_profit", ["100", "99"])
    def test_take_profit_at_or_below_price_is_invalid(self, take_profit):
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, take_profit=Decimal(take_profit))

        assert result.error.code == "ORDER_INVALID_TAKE_PROFIT"
        assert result.error.http_status == 422
        _assert_nothing_created(mocks)

    def test_rr_below_min_ratio_is_rejected(self):
        # precio 100, SL 95 (riesgo 5), TP 105 (beneficio 5) → R/R 1 < 2
        service, mocks = _make_service(bot=_make_bot())

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("105"))

        assert result.error.code == "ORDER_PROTECTION_RR_TOO_LOW"
        assert result.error.http_status == 422
        assert result.error.meta == {"ratio": "1.00", "min": "2"}
        _assert_nothing_created(mocks)

    def test_rr_equal_to_min_ratio_passes(self):
        # precio 100, SL 95 (riesgo 5), TP 110 (beneficio 10) → R/R 2
        service, _ = _make_service(bot=_make_bot())

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("110"))

        assert result.success is True

    def test_position_with_native_stop_returns_native_stop_active(self):
        position = _make_position(qty="1", sl_order_id=77)
        service, mocks = _make_service(bot=_make_bot(mode="live"), position=position)

        result = _buy(service, stop_loss=Decimal("95"))

        assert result.error.code == "ORDER_NATIVE_STOP_ACTIVE"
        assert result.error.http_status == 409
        _assert_nothing_created(mocks)


# ======================================================================
# TestManualProtectionApplied
# ======================================================================

class TestManualProtectionApplied:
    def test_success_sets_protection_on_new_position(self):
        service, mocks = _make_service(bot=_make_bot(), position=None)

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("110"))

        assert result.success is True
        position = mocks.position_repo.create.call_args.args[0]
        assert position.stop_loss == Decimal("95")
        assert position.take_profit == Decimal("110")
        assert position.signal_id is None
        mocks.position_repo.commit.assert_called_once()

    def test_take_profit_only_keeps_existing_stop_loss_and_signal(self):
        # Comprar más con solo TP no borra el SL de la señal que abrió la posición
        position = _make_position(qty="1")
        position.signal_id = 55
        position.stop_loss = Decimal("90")
        service, _ = _make_service(bot=_make_bot(), position=position)

        _buy(service, take_profit=Decimal("120"))

        assert position.take_profit == Decimal("120")
        assert position.stop_loss == Decimal("90")
        assert position.signal_id == 55

    def test_live_with_place_native_stop_places_sl_on_exchange(self):
        bot = _make_bot(mode="live")
        service, mocks = _make_service(bot=bot, position=None, place_native_stop=True)

        _buy(service, stop_loss=Decimal("95"))

        position = mocks.position_repo.create.call_args.args[0]
        mocks.native_stop.place.assert_called_once_with(bot, position, Decimal("95"))

    def test_live_without_place_native_stop_does_not_place_sl(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"), position=None, place_native_stop=False
        )

        _buy(service, stop_loss=Decimal("95"))

        mocks.native_stop.place.assert_not_called()

    def test_paper_never_places_native_sl(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="paper"), position=None, place_native_stop=True
        )

        _buy(service, stop_loss=Decimal("95"))

        mocks.native_stop.place.assert_not_called()

    def test_take_profit_only_does_not_place_native_sl(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"), position=None, place_native_stop=True
        )

        _buy(service, take_profit=Decimal("120"))

        mocks.native_stop.place.assert_not_called()

    def test_failed_buy_does_not_apply_protection(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"),
            exec_error=RuntimeError("rejected"),
            place_native_stop=True,
        )

        _buy(service, stop_loss=Decimal("95"))

        mocks.position_repo.commit.assert_not_called()
        mocks.native_stop.place.assert_not_called()

    def test_without_protection_params_position_is_not_protected(self):
        service, mocks = _make_service(bot=_make_bot(mode="live"), place_native_stop=True)

        _buy(service)

        position = mocks.position_repo.create.call_args.args[0]
        assert position.stop_loss is None
        assert position.take_profit is None
        mocks.native_stop.place.assert_not_called()
        mocks.position_repo.commit.assert_not_called()


# ======================================================================
# TestPendingProtection
# ======================================================================

class TestPendingProtection:
    """
    Si la compra no se ejecuta al instante (sent / sin respuesta), el SL/TP
    queda pendiente en `meta.protection` y lo aplica la reconciliación.
    """

    def test_live_buy_sent_without_fill_stores_pending_protection(self):
        position = _make_position(qty="0")
        service, mocks = _make_service(
            bot=_make_bot(mode="live"),
            position=position,
            exec_result=ExecutionResult(status="sent", exchange_order_id="ex-9"),
            place_native_stop=True,
        )

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("110"))

        assert result.success is True
        assert result.data.status == "sent"
        assert result.data.meta["protection"] == {"stop_loss": "95", "take_profit": "110"}
        assert position.stop_loss is None
        assert position.take_profit is None
        mocks.position_repo.update.assert_not_called()
        mocks.position_repo.commit.assert_not_called()
        mocks.native_stop.place.assert_not_called()

    def test_pending_protection_keeps_none_for_missing_side(self):
        service, _ = _make_service(
            bot=_make_bot(mode="live"),
            exec_result=ExecutionResult(status="sent", exchange_order_id="ex-9"),
        )

        result = _buy(service, take_profit=Decimal("110"))

        assert result.data.meta["protection"] == {"stop_loss": None, "take_profit": "110"}

    def test_uncertain_error_also_stores_pending_protection(self):
        service, mocks = _make_service(
            bot=_make_bot(mode="live"),
            exec_error=ExecutionUncertainError("timeout"),
            place_native_stop=True,
        )

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("110"))

        assert result.success is False
        assert result.error.code == "ORDER_EXECUTION_UNCERTAIN"
        order = mocks.created_orders[0]
        assert order.status == "sent"
        assert order.meta["needs_reconciliation"] is True
        assert order.meta["protection"] == {"stop_loss": "95", "take_profit": "110"}
        mocks.native_stop.place.assert_not_called()

    def test_buy_without_protection_does_not_store_pending_protection(self):
        service, _ = _make_service(
            bot=_make_bot(mode="live"),
            exec_result=ExecutionResult(status="sent", exchange_order_id="ex-9"),
        )

        result = _buy(service)

        assert "protection" not in result.data.meta

    def test_filled_buy_does_not_store_pending_protection(self):
        service, _ = _make_service(bot=_make_bot(), position=None)

        result = _buy(service, stop_loss=Decimal("95"), take_profit=Decimal("110"))

        assert "protection" not in result.data.meta

    def test_signal_buy_with_protection_links_signal_to_position(self):
        service, mocks = _make_service(bot=_make_bot(), position=None, signal=_make_signal())

        result = _buy(
            service, signal_id=55, stop_loss=Decimal("95"), take_profit=Decimal("110")
        )

        assert result.success is True
        position = mocks.position_repo.create.call_args.args[0]
        assert position.signal_id == 55
        assert position.stop_loss == Decimal("95")
        assert position.take_profit == Decimal("110")
