# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_live_executor.py
#
# Tests unitarios del LiveExecutor (M8) con ccxt mockeado.
#
# ESTRATEGIA:
# - Nunca se llama a un exchange real: `LiveExecutor._build_client` se
#   reemplaza por un lambda que devuelve un cliente MagicMock.
# - Las excepciones son las clases reales de ccxt, para probar la
#   traducción a RuntimeError / ExecutionUncertainError.
#
# CUBRE:
# - _to_result: mapeo de estados, precio (average / cost ÷ filled), fee.
# - _send: traducción de errores de ccxt.
# - execute / fetch / cancel / place_stop_loss.
# - _order_symbol: símbolo obligatorio.
# - Perpetuos (2026-10-26): reduceOnly en ventas y stop loss, margen
#   aislado y 1x una vez por cuenta y símbolo, margen libre de Futuros,
#   modo Hedge rechazado, precisión y mínimos, comisión por trades.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import ccxt
import pytest

from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor


# ======================================================================
# Helpers
# ======================================================================

def _make_order(
    qty: str = "2",
    side: str = "buy",
    type: str = "market",
    price: str | None = None,
    stop_price: str | None = None,
    exchange_order_id: str | None = None,
    client_order_id: str | None = "ta-1",
    symbol: str | None = "BTC/USDT",
) -> Order:
    meta = {"mode": "live"}
    if symbol is not None:
        meta["symbol"] = symbol
    return Order(
        id=1,
        bot_id=10,
        side=side,
        type=type,
        qty=Decimal(qty),
        status="new",
        price=Decimal(price) if price is not None else None,
        stop_price=Decimal(stop_price) if stop_price is not None else None,
        exchange_order_id=exchange_order_id,
        client_order_id=client_order_id,
        meta=meta,
    )


def _make_executor(monkeypatch, client: MagicMock | None = None):
    """Retorna (executor, client) con _build_client parcheado."""
    client = client or MagicMock()
    client.id = "binance"
    # Mercado sin mínimos y precisión que no cambia la cantidad
    client.market.return_value = {"limits": {}}
    client.amount_to_precision.side_effect = lambda symbol, amount: str(amount)
    client.fetch_position_mode.return_value = {"hedged": False}
    monkeypatch.setattr(LiveExecutor, "_build_client", lambda self, bot: client)
    LiveExecutor._prepared.clear()
    executor = LiveExecutor(
        account_repo=MagicMock(),
        exchange_repo=MagicMock(),
    )
    return executor, client


BOT = MagicMock()


# ======================================================================
# TestToResult
# ======================================================================

class TestToResult:

    def test_fully_filled_with_average_returns_filled_and_fill(self):
        order = _make_order(qty="2")
        response = {
            "id": "abc123", "status": "closed", "filled": 2.0,
            "average": 100.5, "price": 100.0,
            "fee": {"cost": 0.2, "currency": "USDT"},
        }

        result = LiveExecutor._to_result(order, response)

        assert result.status == "filled"
        assert result.exchange_order_id == "abc123"
        assert result.fill is not None
        assert result.fill.qty == Decimal("2.0")
        assert result.fill.price == Decimal("100.5")
        assert result.fill.fee == Decimal("0.2")
        assert result.fill.fee_asset == "USDT"
        assert result.fill.order_id == order.id
        assert result.fill.exchange_trade_id == "abc123"

    def test_partial_fill_returns_partially_filled(self):
        order = _make_order(qty="2")
        response = {"id": "x", "status": "open", "filled": 0.5, "average": 100}

        result = LiveExecutor._to_result(order, response)

        assert result.status == "partially_filled"
        assert result.fill.qty == Decimal("0.5")

    def test_open_without_fill_returns_sent_without_fill(self):
        # Límite lejos del precio: aceptada pero sin ejecutar
        order = _make_order(qty="2", type="limit", price="90")
        response = {"id": "x", "status": "open", "filled": 0.0, "price": 90}

        result = LiveExecutor._to_result(order, response)

        assert result.status == "sent"
        assert result.fill is None
        assert result.exchange_order_id == "x"

    def test_unknown_status_without_fill_returns_sent(self):
        order = _make_order()

        result = LiveExecutor._to_result(order, {"id": "x", "filled": None})

        assert result.status == "sent"
        assert result.fill is None

    @pytest.mark.parametrize(
        "ccxt_status, expected",
        [
            ("canceled", "canceled"),
            ("cancelled", "canceled"),
            ("rejected", "rejected"),
            ("expired", "rejected"),
        ],
    )
    def test_closed_without_execution_maps_final_status(self, ccxt_status, expected):
        order = _make_order()
        response = {"id": "x", "status": ccxt_status, "filled": 0}

        result = LiveExecutor._to_result(order, response)

        assert result.status == expected
        assert result.fill is None

    def test_uses_cost_divided_by_filled_when_no_average_nor_price(self):
        order = _make_order(qty="2")
        response = {"id": "x", "status": "closed", "filled": 2, "average": None,
                    "price": None, "cost": 201}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.price == Decimal("100.5")

    def test_prefers_cost_over_limit_price_when_average_missing(self):
        # Límite de compra a 100 ejecutada a 99 (mejor precio): el fill real es 99
        order = _make_order(qty="2", type="limit", price="100")
        response = {"id": "x", "status": "closed", "filled": 2, "average": None,
                    "price": 100, "cost": 198}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.price == Decimal("99")

    def test_closed_without_filled_uses_amount(self):
        order = _make_order(qty="2")
        response = {"id": "x", "status": "closed", "filled": None,
                    "amount": 1.5, "average": 100}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.qty == Decimal("1.5")
        assert result.status == "partially_filled"

    def test_closed_without_filled_nor_amount_uses_order_qty(self):
        order = _make_order(qty="2")
        response = {"id": "x", "status": "closed", "filled": None, "average": 100}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.qty == Decimal("2")
        assert result.status == "filled"

    def test_filled_without_price_raises_uncertain(self):
        # Nunca se inventa precio 0
        order = _make_order(qty="2")
        response = {"id": "x", "status": "closed", "filled": 2,
                    "average": None, "price": None, "cost": None}

        with pytest.raises(ExecutionUncertainError):
            LiveExecutor._to_result(order, response)

    def test_missing_fee_defaults_to_zero(self):
        order = _make_order(qty="1")
        response = {"id": "x", "status": "closed", "filled": 1, "average": 100, "fee": None}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.fee == Decimal("0")
        assert result.fill.fee_asset is None

    def test_fee_without_cost_defaults_to_zero(self):
        order = _make_order(qty="1")
        response = {"id": "x", "status": "closed", "filled": 1, "average": 100,
                    "fee": {"cost": None, "currency": "BNB"}}

        result = LiveExecutor._to_result(order, response)

        assert result.fill.fee == Decimal("0")
        assert result.fill.fee_asset == "BNB"

    def test_missing_id_gives_none_exchange_order_id(self):
        order = _make_order()

        result = LiveExecutor._to_result(order, {"id": None, "status": "open", "filled": 0})

        assert result.exchange_order_id is None

    def test_numeric_id_is_stringified(self):
        order = _make_order()

        result = LiveExecutor._to_result(order, {"id": 987, "status": "open", "filled": 0})

        assert result.exchange_order_id == "987"


# ======================================================================
# TestSendErrorTranslation
# ======================================================================

class TestSendErrorTranslation:

    def _raise(self, exc: Exception):
        def call():
            raise exc
        return call

    def test_returns_response_on_success(self):
        assert LiveExecutor._send(lambda: {"id": "1"}) == {"id": "1"}

    @pytest.mark.parametrize(
        "exc",
        [
            ccxt.InsufficientFunds("sin saldo"),
            ccxt.InvalidOrder("cantidad mínima"),
            ccxt.ExchangeError("error genérico"),
        ],
    )
    def test_rejections_become_runtime_error(self, exc):
        with pytest.raises(RuntimeError) as info:
            LiveExecutor._send(self._raise(exc))

        # Debe ser rechazo seguro, no incierto
        assert not isinstance(info.value, ExecutionUncertainError)

    @pytest.mark.parametrize(
        "exc",
        [
            ccxt.RequestTimeout("timeout"),
            ccxt.NetworkError("red caída"),
            ValueError("algo inesperado"),
        ],
    )
    def test_network_and_unknown_errors_become_uncertain(self, exc):
        with pytest.raises(ExecutionUncertainError):
            LiveExecutor._send(self._raise(exc))


# ======================================================================
# TestOrderSymbol
# ======================================================================

class TestOrderSymbol:

    def test_returns_spot_symbol(self):
        assert LiveExecutor._order_symbol(_make_order(symbol="BTC/USDT")) == "BTC/USDT"

    def test_accepts_perpetual(self):
        assert LiveExecutor._order_symbol(_make_order(symbol="XAU/USDT:USDT")) == "XAU/USDT:USDT"

    def test_rejects_missing_symbol(self):
        with pytest.raises(RuntimeError):
            LiveExecutor._order_symbol(_make_order(symbol=None))


# ======================================================================
# TestExecute
# ======================================================================

class TestExecute:

    def test_sends_order_with_client_order_id_and_returns_result(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.create_order.return_value = {
            "id": "ex-1", "status": "closed", "filled": 2, "average": 100,
        }
        order = _make_order(qty="2", client_order_id="ta-1")

        result = executor.execute(order, BOT)

        assert result.status == "filled"
        kwargs = client.create_order.call_args.kwargs
        assert kwargs["symbol"] == "BTC/USDT"
        assert kwargs["side"] == "buy"
        assert kwargs["type"] == "market"
        assert kwargs["amount"] == 2.0
        assert kwargs["price"] is None
        assert kwargs["params"]["clientOrderId"] == "ta-1"

    def test_limit_order_sends_price_and_stop_price(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.create_order.return_value = {"id": "ex-1", "status": "open", "filled": 0}
        order = _make_order(type="stop_limit", price="95", stop_price="96")

        result = executor.execute(order, BOT)

        assert result.status == "sent"
        kwargs = client.create_order.call_args.kwargs
        assert kwargs["price"] == 95.0
        assert kwargs["params"]["stopPrice"] == 96.0

    def test_perpetual_buy_sets_isolated_1x_once_and_checks_margin(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_balance.return_value = {"USDT": {"free": 1000}}
        client.create_order.return_value = {"id": "p-1", "status": "closed", "filled": 2, "average": 100}
        order = _make_order(qty="2", symbol="XAU/USDT:USDT")
        order.meta["reference_price"] = "100"

        executor.execute(order, BOT)
        executor.execute(_make_order(qty="2", symbol="XAU/USDT:USDT"), BOT)

        client.set_margin_mode.assert_called_once_with("isolated", "XAU/USDT:USDT")
        client.set_leverage.assert_called_once_with(1, "XAU/USDT:USDT")
        client.fetch_balance.assert_called_once_with({"type": "future"})
        assert "reduceOnly" not in client.create_order.call_args.kwargs["params"]

    def test_perpetual_buy_without_margin_is_rejected(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_balance.return_value = {"USDT": {"free": 50}}
        order = _make_order(qty="2", symbol="XAU/USDT:USDT")
        order.meta["reference_price"] = "100"

        with pytest.raises(RuntimeError) as info:
            executor.execute(order, BOT)

        assert "Futuros" in str(info.value)
        client.create_order.assert_not_called()

    def test_perpetual_hedge_mode_is_rejected(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_position_mode.return_value = {"hedged": True}

        with pytest.raises(RuntimeError):
            executor.execute(_make_order(symbol="XAU/USDT:USDT"), BOT)

        client.create_order.assert_not_called()

    def test_perpetual_sell_is_reduce_only_without_preparing(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.create_order.return_value = {"id": "p-2", "status": "closed", "filled": 2, "average": 100}

        executor.execute(_make_order(side="sell", symbol="XAU/USDT:USDT"), BOT)

        assert client.create_order.call_args.kwargs["params"]["reduceOnly"] is True
        client.set_leverage.assert_not_called()

    def test_amount_is_rounded_to_market_precision(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.amount_to_precision.side_effect = lambda symbol, amount: "0.123"
        client.create_order.return_value = {"id": "x", "status": "closed", "filled": 0.123, "average": 100}
        order = _make_order(qty="0.123456")

        result = executor.execute(order, BOT)

        assert client.create_order.call_args.kwargs["amount"] == 0.123
        assert order.qty == Decimal("0.123")
        assert result.status == "filled"

    def test_buy_below_exchange_minimum_is_rejected(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.market.return_value = {"limits": {"cost": {"min": 5}}}
        order = _make_order(qty="0.01")
        order.meta["reference_price"] = "100"

        with pytest.raises(RuntimeError):
            executor.execute(order, BOT)

        client.create_order.assert_not_called()

    def test_missing_fee_is_read_from_order_trades(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.has = {"fetchOrderTrades": True}
        client.create_order.return_value = {"id": "p-3", "status": "closed", "filled": 2, "average": 100, "fee": None}
        client.fetch_order_trades.return_value = [
            {"fee": {"cost": 0.04, "currency": "USDT"}},
            {"fee": {"cost": 0.06, "currency": "USDT"}},
        ]

        result = executor.execute(_make_order(side="sell", symbol="XAU/USDT:USDT"), BOT)

        assert result.fill.fee == Decimal("0.1")
        assert result.fill.fee_asset == "USDT"

    def test_timeout_raises_uncertain(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.create_order.side_effect = ccxt.RequestTimeout("timeout")

        with pytest.raises(ExecutionUncertainError):
            executor.execute(_make_order(), BOT)


# ======================================================================
# TestFetch
# ======================================================================

class TestFetch:

    def test_fetches_by_exchange_order_id(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.return_value = {"id": "ex-1", "status": "open"}
        order = _make_order(exchange_order_id="ex-1")

        result = executor.fetch(order, BOT)

        assert result == {"id": "ex-1", "status": "open"}
        client.fetch_order.assert_called_once_with("ex-1", "BTC/USDT")

    def test_fetches_by_client_order_id_without_exchange_id(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.return_value = {"id": "ex-1", "clientOrderId": "ta-1"}
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        result = executor.fetch(order, BOT)

        assert result["id"] == "ex-1"
        client.fetch_order.assert_called_once_with(
            None, "BTC/USDT", {"clientOrderId": "ta-1"}
        )

    def test_returns_none_without_any_id(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        order = _make_order(exchange_order_id=None, client_order_id=None)

        assert executor.fetch(order, BOT) is None
        client.fetch_order.assert_not_called()

    @pytest.mark.parametrize(
        "exc",
        [ccxt.ArgumentsRequired("id requerido"), ccxt.NotSupported("no"), ccxt.BadRequest("bad")],
    )
    def test_falls_back_to_open_orders_when_filter_unsupported(self, monkeypatch, exc):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = exc
        client.fetch_open_orders.return_value = [
            {"id": "otra", "clientOrderId": "ta-99"},
            {"id": "ex-1", "clientOrderId": "ta-1"},
        ]
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        result = executor.fetch(order, BOT)

        assert result["id"] == "ex-1"
        client.fetch_closed_orders.assert_not_called()

    def test_falls_back_to_closed_orders_when_not_open(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.NotSupported("no")
        client.fetch_open_orders.return_value = []
        client.fetch_closed_orders.return_value = [{"id": "ex-1", "clientOrderId": "ta-1"}]
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        result = executor.fetch(order, BOT)

        assert result["id"] == "ex-1"

    def test_fallback_skips_unsupported_listing_methods(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.ArgumentsRequired("id requerido")
        client.fetch_open_orders.side_effect = ccxt.NotSupported("no")
        client.fetch_closed_orders.return_value = [{"id": "ex-1", "clientOrderId": "ta-1"}]
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        result = executor.fetch(order, BOT)

        assert result["id"] == "ex-1"

    def test_fallback_returns_none_when_not_found_anywhere(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.NotSupported("no")
        client.fetch_open_orders.return_value = [{"id": "otra", "clientOrderId": "ta-99"}]
        client.fetch_closed_orders.return_value = None
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        assert executor.fetch(order, BOT) is None

    def test_order_not_found_returns_none(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.OrderNotFound("no existe")
        order = _make_order(exchange_order_id="ex-1")

        assert executor.fetch(order, BOT) is None

    def test_order_not_found_by_client_id_returns_none(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.OrderNotFound("no existe")
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        assert executor.fetch(order, BOT) is None
        client.fetch_open_orders.assert_not_called()

    @pytest.mark.parametrize("exc", [ccxt.RequestTimeout("t"), ccxt.NetworkError("n")])
    def test_network_error_raises_uncertain(self, monkeypatch, exc):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = exc
        order = _make_order(exchange_order_id="ex-1")

        with pytest.raises(ExecutionUncertainError):
            executor.fetch(order, BOT)

    def test_network_error_during_fallback_raises_uncertain(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.NotSupported("no")
        client.fetch_open_orders.side_effect = ccxt.NetworkError("red")
        order = _make_order(exchange_order_id=None, client_order_id="ta-1")

        with pytest.raises(ExecutionUncertainError):
            executor.fetch(order, BOT)

    def test_exchange_error_raises_runtime_error(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.fetch_order.side_effect = ccxt.ExchangeError("boom")
        order = _make_order(exchange_order_id="ex-1")

        with pytest.raises(RuntimeError) as info:
            executor.fetch(order, BOT)

        assert not isinstance(info.value, ExecutionUncertainError)


# ======================================================================
# TestCancel
# ======================================================================

class TestCancel:

    def test_without_exchange_id_returns_false_without_calling_exchange(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        order = _make_order(exchange_order_id=None)

        assert executor.cancel(order, BOT) is False
        client.cancel_order.assert_not_called()

    def test_success_returns_true(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        order = _make_order(exchange_order_id="ex-1")

        assert executor.cancel(order, BOT) is True
        client.cancel_order.assert_called_once_with("ex-1", "BTC/USDT")

    def test_order_not_found_returns_false(self, monkeypatch):
        # Ya ejecutada o cancelada antes
        executor, client = _make_executor(monkeypatch)
        client.cancel_order.side_effect = ccxt.OrderNotFound("no existe")
        order = _make_order(exchange_order_id="ex-1")

        assert executor.cancel(order, BOT) is False

    @pytest.mark.parametrize("exc", [ccxt.RequestTimeout("t"), ccxt.NetworkError("n")])
    def test_network_error_raises_uncertain(self, monkeypatch, exc):
        executor, client = _make_executor(monkeypatch)
        client.cancel_order.side_effect = exc
        order = _make_order(exchange_order_id="ex-1")

        with pytest.raises(ExecutionUncertainError):
            executor.cancel(order, BOT)

    def test_exchange_error_raises_runtime_error(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.cancel_order.side_effect = ccxt.ExchangeError("boom")
        order = _make_order(exchange_order_id="ex-1")

        with pytest.raises(RuntimeError) as info:
            executor.cancel(order, BOT)

        assert not isinstance(info.value, ExecutionUncertainError)


# ======================================================================
# TestPlaceStopLoss
# ======================================================================

class TestPlaceStopLoss:

    def test_without_stop_price_raises_runtime_error(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        order = _make_order(side="sell", type="stop", stop_price=None)

        with pytest.raises(RuntimeError):
            executor.place_stop_loss(order, BOT)

        client.create_stop_loss_order.assert_not_called()

    @pytest.mark.parametrize("has", [{}, {"createStopLossOrder": False}])
    def test_exchange_without_native_stop_raises_runtime_error(self, monkeypatch, has):
        executor, client = _make_executor(monkeypatch)
        client.has = has
        order = _make_order(side="sell", type="stop", stop_price="90")

        with pytest.raises(RuntimeError):
            executor.place_stop_loss(order, BOT)

        client.create_stop_loss_order.assert_not_called()

    def test_success_sends_market_stop_and_returns_sent(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.has = {"createStopLossOrder": True}
        client.create_stop_loss_order.return_value = {
            "id": "sl-1", "status": "open", "filled": 0,
        }
        order = _make_order(qty="1.5", side="sell", type="stop",
                            stop_price="90", client_order_id="ta-7")

        result = executor.place_stop_loss(order, BOT)

        assert result.status == "sent"
        assert result.exchange_order_id == "sl-1"
        assert result.fill is None
        client.create_stop_loss_order.assert_called_once_with(
            "BTC/USDT", "market", "sell", 1.5, None, 90.0, {"clientOrderId": "ta-7"},
        )

    def test_rejection_raises_runtime_error(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.has = {"createStopLossOrder": True}
        client.create_stop_loss_order.side_effect = ccxt.InvalidOrder("stop inválido")
        order = _make_order(side="sell", type="stop", stop_price="90")

        with pytest.raises(RuntimeError) as info:
            executor.place_stop_loss(order, BOT)

        assert not isinstance(info.value, ExecutionUncertainError)

    def test_timeout_raises_uncertain(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.has = {"createStopLossOrder": True}
        client.create_stop_loss_order.side_effect = ccxt.RequestTimeout("timeout")
        order = _make_order(side="sell", type="stop", stop_price="90")

        with pytest.raises(ExecutionUncertainError):
            executor.place_stop_loss(order, BOT)

    def test_perpetual_stop_loss_is_reduce_only(self, monkeypatch):
        executor, client = _make_executor(monkeypatch)
        client.has = {"createStopLossOrder": True}
        client.create_stop_loss_order.return_value = {"id": "sl-2", "status": "open", "filled": 0}
        order = _make_order(side="sell", type="stop", stop_price="90", symbol="XAU/USDT:USDT")

        executor.place_stop_loss(order, BOT)

        params = client.create_stop_loss_order.call_args.args[6]
        assert params["reduceOnly"] is True
