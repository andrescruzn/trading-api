# -*- coding: utf-8 -*-

# ======================================================================
# tests/orders/test_native_stop_service.py
#
# Tests unitarios del NativeStopService (stop loss nativo en live).
#
# ESTRATEGIA:
# - Repositorios y LiveExecutor son MagicMock (nunca se llama a ccxt).
# - `utc_now` se fija en el módulo del servicio.
# - place(): se verifica que la orden se confirma ANTES de enviarla y
#   cómo queda (estado, meta, vínculo con la posición) en cada resultado.
# - cancel(): no hace commit (lo hace el llamador).
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.execution.executor_interface import (
    ExecutionResult,
    ExecutionUncertainError,
)
from app.modules.orders.services.execution import native_stop_service as module
from app.modules.orders.services.execution.native_stop_service import NativeStopService

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
NEW_ORDER_ID = 501


# ======================================================================
# Helpers
# ======================================================================

@pytest.fixture(autouse=True)
def _fixed_now(monkeypatch):
    monkeypatch.setattr(module, "utc_now", lambda: NOW)


def _make_bot() -> Bot:
    return Bot(
        id=1,
        name="Agente live",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode="live",
        status="running",
        risk_params={"risk_pct": 0.01},
    )


def _make_position(sl_order_id: int | None = None) -> Position:
    return Position(
        id=40,
        bot_id=1,
        symbol_id=5,
        qty=Decimal("2"),
        avg_price=Decimal("100"),
        stop_loss=Decimal("90"),
        take_profit=Decimal("130"),
        signal_id=11,
        sl_order_id=sl_order_id,
    )


def _make_stop_order(status: str = "sent") -> Order:
    return Order(
        id=77,
        bot_id=1,
        side="sell",
        type="stop",
        qty=Decimal("2"),
        status=status,
        exchange_order_id="ex-77",
        stop_price=Decimal("90"),
        meta={"symbol": "BTC/USDT", "mode": "live", "reason": "stop_loss_native"},
    )


def _assign_id(order: Order) -> Order:
    order.id = NEW_ORDER_ID
    return order


def _make_service(symbol: MagicMock | None = MagicMock(symbol="BTC/USDT"), stop_order: Order | None = None):
    order_repo = MagicMock()
    order_repo.create.side_effect = _assign_id
    order_repo.update.side_effect = lambda o: o
    order_repo.get_by_id.return_value = stop_order

    position_repo = MagicMock()
    position_repo.update.side_effect = lambda p: p

    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = symbol

    live = MagicMock()

    service = NativeStopService(
        order_repo=order_repo,
        position_repo=position_repo,
        symbol_repo=symbol_repo,
        live_executor=live,
    )
    return service, order_repo, position_repo, live


# ======================================================================
# TestPlace
# ======================================================================

class TestPlace:
    def test_missing_symbol_returns_symbol_not_found(self):
        service, order_repo, _, live = _make_service(symbol=None)

        result = service.place(_make_bot(), _make_position(), Decimal("90"))

        assert result.success is False
        assert result.error.code == "SYMBOL_NOT_FOUND"
        assert result.error.http_status == 404
        order_repo.create.assert_not_called()
        live.place_stop_loss.assert_not_called()

    def test_builds_stop_sell_order_for_position_qty(self):
        service, order_repo, _, live = _make_service()
        live.place_stop_loss.return_value = ExecutionResult(status="sent", exchange_order_id="ex-9")

        service.place(_make_bot(), _make_position(), Decimal("90"))

        created = order_repo.create.call_args.args[0]
        assert created.side == "sell"
        assert created.type == "stop"
        assert created.qty == Decimal("2")
        assert created.stop_price == Decimal("90")
        assert created.ts == NOW
        assert created.meta == {"symbol": "BTC/USDT", "mode": "live", "reason": "stop_loss_native"}

    def test_persists_order_before_sending_it(self):
        service, order_repo, _, live = _make_service()
        seen: dict = {}

        def _place(order, bot):
            seen["commits"] = order_repo.commit.call_count
            seen["status"] = order.status
            seen["client_order_id"] = order.client_order_id
            return ExecutionResult(status="sent", exchange_order_id="ex-9")

        live.place_stop_loss.side_effect = _place

        service.place(_make_bot(), _make_position(), Decimal("90"))

        assert seen == {"commits": 1, "status": "new", "client_order_id": f"ta-{NEW_ORDER_ID}"}

    def test_success_links_position_to_stop_order(self):
        service, order_repo, position_repo, live = _make_service()
        live.place_stop_loss.return_value = ExecutionResult(status="sent", exchange_order_id="ex-9")
        position = _make_position()

        result = service.place(_make_bot(), position, Decimal("90"))

        assert result.success is True
        assert result.data.status == "sent"
        assert result.data.exchange_order_id == "ex-9"
        assert position.sl_order_id == NEW_ORDER_ID
        position_repo.update.assert_called_once_with(position)
        assert order_repo.commit.call_count == 2

    def test_uncertain_error_leaves_sent_with_needs_reconciliation_and_linked(self):
        service, order_repo, _, live = _make_service()
        live.place_stop_loss.side_effect = ExecutionUncertainError("timeout")
        position = _make_position()

        result = service.place(_make_bot(), position, Decimal("90"))

        assert result.success is True
        order = result.data
        assert order.status == "sent"
        assert order.meta["needs_reconciliation"] is True
        assert order.meta["error"] == "timeout"
        assert order.meta["reason"] == "stop_loss_native"
        assert position.sl_order_id == NEW_ORDER_ID
        assert order_repo.commit.call_count == 2

    def test_runtime_error_rejects_order_and_does_not_link(self):
        service, order_repo, position_repo, live = _make_service()
        live.place_stop_loss.side_effect = RuntimeError("binance no soporta stop loss nativo")
        position = _make_position()

        result = service.place(_make_bot(), position, Decimal("90"))

        assert result.success is False
        assert result.error.code == "NATIVE_STOP_FAILED"
        assert result.error.http_status == 502
        assert result.error.meta == {"order_id": NEW_ORDER_ID}
        rejected = order_repo.update.call_args.args[0]
        assert rejected.status == "rejected"
        assert rejected.meta["error"] == "binance no soporta stop loss nativo"
        assert position.sl_order_id is None
        position_repo.update.assert_not_called()
        assert order_repo.commit.call_count == 2


# ======================================================================
# TestCancel
# ======================================================================

class TestCancel:
    def test_without_native_stop_returns_ok(self):
        service, order_repo, position_repo, live = _make_service()

        result = service.cancel(_make_bot(), _make_position(sl_order_id=None))

        assert result.success is True
        order_repo.get_by_id.assert_not_called()
        live.cancel.assert_not_called()
        position_repo.update.assert_not_called()

    def test_missing_stop_order_unlinks_and_returns_ok(self):
        service, _, position_repo, live = _make_service(stop_order=None)
        position = _make_position(sl_order_id=77)

        result = service.cancel(_make_bot(), position)

        assert result.success is True
        assert position.sl_order_id is None
        position_repo.update.assert_called_once_with(position)
        live.cancel.assert_not_called()

    @pytest.mark.parametrize("status", ["canceled", "rejected"])
    def test_finished_stop_order_unlinks_and_returns_ok(self, status):
        service, _, _, live = _make_service(stop_order=_make_stop_order(status=status))
        position = _make_position(sl_order_id=77)

        result = service.cancel(_make_bot(), position)

        assert result.success is True
        assert position.sl_order_id is None
        live.cancel.assert_not_called()

    def test_filled_stop_order_returns_native_stop_active(self):
        service, _, position_repo, live = _make_service(stop_order=_make_stop_order(status="filled"))
        position = _make_position(sl_order_id=77)

        result = service.cancel(_make_bot(), position)

        assert result.success is False
        assert result.error.code == "ORDER_NATIVE_STOP_ACTIVE"
        assert result.error.http_status == 409
        assert position.sl_order_id == 77
        live.cancel.assert_not_called()
        position_repo.update.assert_not_called()

    @pytest.mark.parametrize(
        "error", [ExecutionUncertainError("timeout"), RuntimeError("exchange error")]
    )
    def test_executor_error_returns_native_stop_active(self, error):
        stop_order = _make_stop_order()
        service, order_repo, _, live = _make_service(stop_order=stop_order)
        live.cancel.side_effect = error
        position = _make_position(sl_order_id=77)

        result = service.cancel(_make_bot(), position)

        assert result.error.code == "ORDER_NATIVE_STOP_ACTIVE"
        assert result.error.http_status == 409
        assert position.sl_order_id == 77
        assert stop_order.status == "sent"
        order_repo.update.assert_not_called()

    def test_executor_returns_false_returns_native_stop_active(self):
        stop_order = _make_stop_order()
        service, order_repo, _, live = _make_service(stop_order=stop_order)
        live.cancel.return_value = False
        position = _make_position(sl_order_id=77)

        result = service.cancel(_make_bot(), position)

        assert result.error.code == "ORDER_NATIVE_STOP_ACTIVE"
        assert position.sl_order_id == 77
        assert stop_order.status == "sent"
        order_repo.update.assert_not_called()

    def test_success_cancels_stop_order_and_unlinks_without_commit(self):
        stop_order = _make_stop_order()
        bot = _make_bot()
        service, order_repo, position_repo, live = _make_service(stop_order=stop_order)
        live.cancel.return_value = True
        position = _make_position(sl_order_id=77)

        result = service.cancel(bot, position)

        assert result.success is True
        live.cancel.assert_called_once_with(stop_order, bot)
        assert stop_order.status == "canceled"
        order_repo.update.assert_called_once_with(stop_order)
        assert position.sl_order_id is None
        position_repo.update.assert_called_once_with(position)
        order_repo.commit.assert_not_called()
        position_repo.commit.assert_not_called()
